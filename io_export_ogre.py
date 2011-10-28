bl_info = {
    "name": "Ogre .mesh exporter",
    "author": "Philip Abbet",
    "blender": (2, 5, 9),
    "api": 37702,
    "location": "File > Export",
    "description": "Export Ogre models",
    "warning": "",
    "category": "Import-Export"
}

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper
from mathutils import Vector
from xml.dom import minidom
import mathutils
import os


######################################### EXPORTER #######################################

def swap(vector):
    return mathutils.Vector((vector.x, vector.z, -vector.y))


class Exporter:
    
    def __init__(self):
        pass

    def __del__(self):
        pass
        
    def process(self, filename):
        
        # Retrieve the scene
        scene = bpy.context.scene
        
        # Retrieve the selected meshes
        selected_objects = filter(lambda x: x.type == 'MESH', bpy.context.selected_objects)

        # Create the XML document
        dom = minidom.getDOMImplementation()
        document = dom.createDocument(None, 'mesh', None)
        xml_root = document.documentElement

        xml_sharedgeometry = document.createElement('sharedgeometry')
        xml_sharedgeometry.vertexcount = 0
        
        xml_vertexbuffer = document.createElement('vertexbuffer')
        xml_vertexbuffer.setAttribute('colours_diffuse', 'false')
        xml_vertexbuffer.setAttribute('normals', 'true')
        xml_vertexbuffer.setAttribute('positions', 'true')

        xml_submeshes = document.createElement('submeshes')

        for obj in selected_objects:
            xml_submesh = document.createElement('submesh')
            xml_submesh.setAttribute('material', obj.name)
            xml_submesh.setAttribute('usesharedvertices', 'true')

            xml_faces = document.createElement('faces')
            xml_faces.facescount = 0

            vertices_map = {}
            vertices = obj.data.vertices

            for face in obj.data.faces:
                indices = []

                if face.use_smooth:
                    for vi in face.vertices:
                        if not(vertices_map.has_key(vi)):
                            v = vertices[vi]
                            self._addXMLVertex(document, xml_vertexbuffer, swap(obj.matrix_world * v.co), swap(obj.matrix_world * v.normal))
                            vertices_map[vi] = xml_sharedgeometry.vertexcount
                            xml_sharedgeometry.vertexcount += 1

                        indices.append(vertices_map[vi])
                else:
                    for vi in face.vertices:
                        v = vertices[vi]
                        self._addXMLVertex(document, xml_vertexbuffer, swap(obj.matrix_world * v.co), swap(obj.matrix_world * face.normal))
                        indices.append(xml_sharedgeometry.vertexcount)
                        xml_sharedgeometry.vertexcount += 1

                self._addXMLFace(document, xml_faces, indices[0], indices[1], indices[2])
                if len(indices) > 3:
                    self._addXMLFace(document, xml_faces, indices[0], indices[2], indices[3])
            
            xml_faces.setAttribute('count', str(xml_faces.facescount))
            xml_submesh.appendChild(xml_faces)
            
            xml_submeshes.appendChild(xml_submesh)
        
        xml_sharedgeometry.appendChild(xml_vertexbuffer)
        xml_sharedgeometry.setAttribute('vertexcount', str(xml_sharedgeometry.vertexcount))

        xml_root.appendChild(xml_sharedgeometry)
        xml_root.appendChild(xml_submeshes)
        
        # Write the XML file
        fh = open(filename, 'w', encoding='utf8')
        document.writexml(fh, addindent='    ', newl='\n', encoding='UTF-8')
        fh.close()
        
        return True

    def _addXMLVertex(self, document, xml_parent, pos, normal):
        xml_vertex = document.createElement('vertex')

        xml_position = document.createElement('position')
        xml_position.setAttribute('x', '%6f' % pos.x)
        xml_position.setAttribute('y', '%6f' % pos.y)
        xml_position.setAttribute('z', '%6f' % pos.z)
        xml_vertex.appendChild(xml_position)

        xml_normal = document.createElement('normal')
        xml_normal.setAttribute('x','%6f' % normal.x)
        xml_normal.setAttribute('y','%6f' % normal.y)
        xml_normal.setAttribute('z','%6f' % normal.z)
        xml_vertex.appendChild(xml_normal)

        xml_parent.appendChild(xml_vertex)

    def _addXMLFace(self, document, xml_parent, v1, v2, v3):
        xml_face = document.createElement('face')
        xml_face.setAttribute('v1', str(v1))
        xml_face.setAttribute('v2', str(v2))
        xml_face.setAttribute('v3', str(v3))
        xml_parent.appendChild(xml_face)
        xml_parent.facescount += 1


##################################### BLENDER CLASSES ####################################

class Report_Dialog(bpy.types.Menu):
    bl_label = "Ogre Exporter Results | (see console for full report)"

    message = ""

    def draw(self, context):
        layout = self.layout
        for line in Report_Dialog.message.splitlines():
            layout.label(text=line)
    
    @staticmethod
    def show(message=None):
        if message is not None:
            Report_Dialog.message = message
        print(Report_Dialog.message)
        bpy.ops.wm.call_menu(name='Report_Dialog')

    @staticmethod
    def append(line):
        Report_Dialog.message += line + "\n"


class ExportOgre(bpy.types.Operator, ExportHelper):
    '''Export an Ogre mesh file'''

    bl_idname = "export.ogre_mesh"
    bl_label = "Export Ogre mesh"

    filename_ext = ".mesh.xml"
    filter_glob = StringProperty(default="*.mesh;*.mesh.xml", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        exporter = Exporter()
        exporter.process(self.filepath)
        return {'FINISHED'}


################################## BLENDER REGISTRATION ##################################

def menu_func_export(self, context):
    self.layout.operator(ExportOgre.bl_idname, text="Ogre mesh (.mesh)")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
# 
# exporter = Exporter()
# exporter.process('/Users/pabbet/Projects/tmp/test.mesh.xml')
