import os
import signal
import sys

from Qt import QtCore, QtWidgets

from custom_nodes.auto_graph import AutoGraph

from NodeGraphQt import (
    NodeGraph,
    PropertiesBinWidget,
    NodesTreeWidget,
    NodesPaletteWidget,
)

from custom_nodes.nodes import diffusers_node, loop_node, image_preview_node


class NodeWindow():

    def __init__(self, parent=None):
        super(NodeWindow, self).__init__()
        # create graph controller.
        graph = AutoGraph()
        # set up context menu for the node graph.
        graph.set_context_menu_from_file('../examples/hotkeys/hotkeys.json')
        nodes = [
            image_preview_node.ImagePreviewNode,
            loop_node.LoopNode,
            diffusers_node.DiffusersNode,
        ]
        # registered example nodes.
        graph.register_nodes(nodes)

        # show the node graph widget.
        graph_widget = graph.widget
        graph_widget.resize(1100, 800)
        graph_widget.show()




        # fit nodes to the viewer.
        graph.clear_selection()
        graph.fit_to_selection()

        # Custom builtin widgets from NodeGraphQt
        # ---------------------------------------
        #self.init_test_nodes(graph)
        self.init_test_node(graph)


        # create a node properties bin widget.
        properties_bin = PropertiesBinWidget(node_graph=graph)
        properties_bin.setWindowFlags(QtCore.Qt.Tool)

        # example show the node properties bin widget when a node is double clicked.
        def display_properties_bin(node):
            if not properties_bin.isVisible():
                properties_bin.show()

        # wire function to "node_double_clicked" signal.
        graph.node_double_clicked.connect(display_properties_bin)

        # create a nodes tree widget.
        nodes_tree = NodesTreeWidget(node_graph=graph)
        nodes_tree.set_category_label('nodeGraphQt.nodes', 'Builtin Nodes')
        nodes_tree.set_category_label('nodes.custom.ports', 'Custom Port Nodes')
        nodes_tree.set_category_label('nodes.widget', 'Widget Nodes')
        nodes_tree.set_category_label('nodes.basic', 'Basic Nodes')
        nodes_tree.set_category_label('nodes.group', 'Group Nodes')
        # nodes_tree.show()

        # create a node palette widget.
        nodes_palette = NodesPaletteWidget(node_graph=graph)
        nodes_palette.set_category_label('nodeGraphQt.nodes', 'Builtin Nodes')
        nodes_palette.set_category_label('nodes.custom.ports', 'Custom Port Nodes')
        nodes_palette.set_category_label('nodes.widget', 'Widget Nodes')
        nodes_palette.set_category_label('nodes.basic', 'Basic Nodes')
        nodes_palette.set_category_label('nodes.group', 'Group Nodes')
        # nodes_palette.show()
        print(graph.model.nodes)
        import ctypes
        def print_nodes():
            for node in nodes:
                try:
                    print(node.execute())
                except:
                    print("non excecutable")
    def init_test_nodes(self, graph):
        # create node with custom text color and disable it.
        n_basic_a = graph.create_node(
            'nodes.basic.BasicNodeA', text_color='#feab20')
        n_basic_a.set_disabled(True)

        # create node and set a custom icon.
        n_basic_b = graph.create_node(
            'nodes.basic.BasicNodeB', name='custom icon')
        n_basic_b.set_icon(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'star.png')
        )

        # create node with the custom port shapes.
        n_custom_ports = graph.create_node(
            'nodes.custom.ports.CustomPortsNode', name='custom ports')

        # create node with the embedded QLineEdit widget.
        n_text_input = graph.create_node(
            'nodes.widget.TextInputNode', name='text node', color='#0a1e20')

        # create node with the embedded QCheckBox widgets.
        n_checkbox = graph.create_node(
            'nodes.widget.CheckboxNode', name='checkbox node')

        # create node with the QComboBox widget.
        n_combo_menu = graph.create_node(
            'nodes.widget.DropdownMenuNode', name='combobox node')

        # crete node with the circular design.
        n_circle = graph.create_node(
            'nodes.basic.CircleNode', name='circle node')

        # create group node.
        n_group = graph.create_node('nodes.group.MyGroupNode')

        # make node connections.

        # (connect nodes using the .set_output method)
        n_text_input.set_output(0, n_custom_ports.input(0))
        n_text_input.set_output(0, n_checkbox.input(0))
        n_text_input.set_output(0, n_combo_menu.input(0))
        # (connect nodes using the .set_input method)
        n_group.set_input(0, n_custom_ports.output(1))
        n_basic_b.set_input(2, n_checkbox.output(0))
        n_basic_b.set_input(2, n_combo_menu.output(1))
        # (connect nodes using the .connect_to method from the port object)
        port = n_basic_a.input(0)
        port.connect_to(n_basic_b.output(0))

        # auto layout nodes.
        graph.auto_layout_nodes()

        # crate a backdrop node and wrap it around
        # "custom port node" and "group node".
        n_backdrop = graph.create_node('Backdrop')
        n_backdrop.wrap_nodes([n_custom_ports, n_combo_menu])
    def init_test_node(self, graph):
        # create node with custom text color and disable it.
        image_node_1 = graph.create_node(
            'nodes.widget.DiffusersNode', text_color='#feab20')
        image_node_1.set_disabled(False)
        # auto layout nodes.
        graph.auto_layout_nodes()


if __name__ == '__main__':

    # handle SIGINT to make the app terminate on CTRL+C
    #signal.signal(signal.SIGINT, signal.SIG_DFL)

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    app = QtWidgets.QApplication([])
    nodeWindow = NodeWindow()
    sys.exit(app.exec_())
