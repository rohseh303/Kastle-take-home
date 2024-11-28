from django.test import TestCase
from tree_manager.models import (
    Tree,
    TreeNode,
    TreeEdge,
    Tag,
    TreeVersion,
    TreeNodeVersion,
    TreeEdgeVersion,
)
from django.utils import timezone

class ConfigurationManagementTestCase(TestCase):
    def setUp(self):
        # Create a tree for testing
        self.tree = Tree.objects.create(name="Configuration Tree")

        # Create initial nodes
        self.node1 = TreeNode.objects.create(tree=self.tree, data={"name": "Node1"})
        self.node2 = TreeNode.objects.create(tree=self.tree, data={"name": "Node2"})

        # Tag the initial version (this will create a TreeVersion)
        self.tree.create_tag(name="initial", description="Initial version")

    def test_configuration_management(self):
        # Retrieve the version associated with the "initial" tag
        initial_tag = self.tree.tags.get(name="initial")
        initial_version = self.tree.versions.get(tag=initial_tag)

        # Making changes to the configuration
        modified_version = self.tree.create_new_tree_version_from_tag("initial")

        # Adding a new node to the modified version
        new_node_version = modified_version.add_node(data={"setting": "new_value"})

        # Adding an edge between nodes
        modified_version.add_edge(
            incoming_node_id=self.node1.id,
            outgoing_node_id=self.node2.id,
            data={"weight": 0.5}
        )

        # Creating a new tag after modifications
        modified_version.tag = self.tree.tags.create(
            name="release-v1.1",
            description="Added new setting"
        )
        modified_version.save()

# class FeatureBranchingTestCase(TestCase):
#     def setUp(self):
#         # Create a tree and tag main version
#         self.tree = Tree.objects.create(name="Main Tree")
#         self.node_main = TreeNode.objects.create(tree=self.tree, data={"main": True})
#         self.main_version = TreeVersion.objects.create(tree=self.tree)
#         self.main_version.add_existing_node(self.node_main, data=self.node_main.data)
#         self.tree.create_tag(name="main-v2.0", description="Main version 2.0", version=self.main_version)

#     def test_feature_branching(self):
#         # Creating a feature branch
#         feature_branch_version = self.tree.create_new_tree_version_from_tag("main-v2.0")
#         self.assertIsNotNone(feature_branch_version)

#         # Making feature-specific changes
#         node1_version = feature_branch_version.add_node(data={"feature_flag": True})
#         node2_version = feature_branch_version.add_node(data={"config": "new_setting"})
#         self.assertIsNotNone(node1_version)
#         self.assertIsNotNone(node2_version)

#         # Adding an edge between the new nodes
#         edge_version = feature_branch_version.add_edge(
#             incoming_node_id=node1_version.node.id,
#             outgoing_node_id=node2_version.node.id,
#             data={"relation": "depends_on"}
#         )
#         self.assertIsNotNone(edge_version)
#         self.assertEqual(edge_version.data, {"relation": "depends_on"})

#         # Tagging the feature branch
#         feature_branch_version.tag = self.tree.tags.create(
#             name="feature-x-v1",
#             description="Feature X implementation"
#         )
#         feature_branch_version.save()
#         self.assertEqual(feature_branch_version.tag.name, "feature-x-v1")

# class RollbackScenarioTestCase(TestCase):
#     def setUp(self):
#         # Create a tree and tag a stable version
#         self.tree = Tree.objects.create(name="Stable Tree")
#         self.node_stable = TreeNode.objects.create(tree=self.tree, data={"stable": True})
#         self.stable_version = TreeVersion.objects.create(tree=self.tree)
#         self.stable_version.add_existing_node(self.node_stable, data=self.node_stable.data)
#         self.tree.create_tag(name="stable-v1", description="Stable version", version=self.stable_version)

#     def test_rollback_scenario(self):
#         # Making potentially risky changes
#         modified_version = self.tree.create_new_tree_version_from_tag("stable-v1")
#         new_node_version = modified_version.add_node(data={"experimental": True})
#         self.assertIsNotNone(new_node_version)

#         edge_version = modified_version.add_edge(
#             incoming_node_id=self.node_stable.id,
#             outgoing_node_id=new_node_version.node.id,
#             data={"type": "experimental"}
#         )
#         self.assertIsNotNone(edge_version)

#         # Simulate problem detection
#         problems_detected = True  # Replace with actual condition in real scenarios

#         if problems_detected:
#             # Rolling back if issues are found
#             rollback_version = modified_version.restore_from_tag("stable-v1")
#             self.assertEqual(rollback_version.tag.name, "stable-v1")
#             # Ensure the experimental node is not present in the rollback version
#             with self.assertRaises(TreeNodeVersion.DoesNotExist):
#                 rollback_version.get_node(new_node_version.node.id)

# class TreeFetchingByTagTestCase(TestCase):
#     def setUp(self):
#         # Create a tree and tag it
#         self.tree = Tree.objects.create(name="Historical Tree")
#         self.node1 = TreeNode.objects.create(tree=self.tree, data={"value": 1})
#         self.node2 = TreeNode.objects.create(tree=self.tree, data={"value": 2})
#         self.node3 = TreeNode.objects.create(tree=self.tree, data={"value": 3})
#         self.node4 = TreeNode.objects.create(tree=self.tree, data={"value": 4})
#         self.node5 = TreeNode.objects.create(tree=self.tree, data={"value": 5})

#         self.version = TreeVersion.objects.create(tree=self.tree)
#         self.version.add_existing_node(self.node1, data=self.node1.data)
#         self.version.add_existing_node(self.node2, data=self.node2.data)
#         self.version.add_existing_node(self.node3, data=self.node3.data)
#         self.version.add_existing_node(self.node4, data=self.node4.data)
#         self.version.add_existing_node(self.node5, data=self.node5.data)

#         # Create edges
#         self.version.add_edge(self.node1.id, self.node2.id, data={"relation": "child"})
#         self.version.add_edge(self.node2.id, self.node3.id, data={"relation": "child"})
#         self.version.add_edge(self.node2.id, self.node4.id, data={"relation": "child"})
#         self.version.add_edge(self.node4.id, self.node5.id, data={"relation": "child"})

#         # Tag the version
#         self.tree.create_tag(name="release-v1.0", description="Release version 1.0", version=self.version)

#     def test_tree_fetching_by_tag(self):
#         # Get a tree by its tag
#         historical_version = self.tree.get_by_tag("release-v1.0")
#         self.assertEqual(historical_version.tag.name, "release-v1.0")

#         # Get the root node(s)
#         root_nodes = historical_version.get_root_nodes()
#         self.assertEqual(len(root_nodes), 1)
#         root_node = root_nodes[0]
#         self.assertEqual(root_node.node.id, self.node1.id)

#         # Traverse from a specific node
#         node = historical_version.get_node(node_id=self.node1.id)
#         self.assertIsNotNone(node)
#         self.assertEqual(node.node.id, self.node1.id)

#         children = historical_version.get_child_nodes(node_id=self.node1.id)
#         self.assertEqual(len(children), 1)
#         self.assertEqual(children[0].node.id, self.node2.id)

#         parents = historical_version.get_parent_nodes(node_id=self.node3.id)
#         self.assertEqual(len(parents), 1)
#         self.assertEqual(parents[0].node.id, self.node2.id)

#         # Get edge information
#         edges = historical_version.get_node_edges(node_id=self.node2.id)
#         self.assertEqual(len(edges), 3)  # 1 incoming, 2 outgoing

#         for edge_version in edges:
#             edge = edge_version.edge
#             connected_node_id = (
#                 edge.outgoing_node.id if edge.incoming_node.id == self.node2.id else edge.incoming_node.id
#             )
#             print(f"Edge {edge_version.id} metadata: {edge_version.data}")
#             print(f"Connected to node: {connected_node_id}")

#         # Traverse entire tree structure
#         def traverse_tree(version, node_id, visited=None):
#             if visited is None:
#                 visited = set()
#             if node_id in visited:
#                 return
#             visited.add(node_id)
#             node_version = version.get_node(node_id)
#             print(f"Node {node_id} metadata: {node_version.data}")
#             edges = version.get_node_edges(node_id)
#             for edge_version in edges:
#                 edge = edge_version.edge
#                 if edge.incoming_node.id == node_id:
#                     next_node_id = edge.outgoing_node.id
#                     if next_node_id not in visited:
#                         print(f"Edge metadata: {edge_version.data}")
#                         traverse_tree(version, next_node_id, visited)

#         # Start traversal from root
#         for root in historical_version.get_root_nodes():
#             traverse_tree(historical_version, root.node.id)

#         # Get all nodes at a specific depth
#         level_2_nodes = historical_version.get_nodes_at_depth(2)
#         level_2_node_ids = [nv.node.id for nv in level_2_nodes]
#         self.assertIn(self.node3.id, level_2_node_ids)
#         self.assertIn(self.node4.id, level_2_node_ids)

#         # Find path between nodes
#         path = historical_version.find_path(start_node_id=self.node1.id, end_node_id=self.node5.id)
#         self.assertIsNotNone(path)
#         expected_path = [self.node1.id, self.node2.id, self.node4.id, self.node5.id]
#         actual_path = [node_id for node_id, _ in path]
#         self.assertEqual(actual_path, expected_path)

#         for node_id, edge_version in path:
#             node_version = historical_version.get_node(node_id)
#             print(f"Node: {node_version.data}")
#             if edge_version:
#                 print(f"Connected by edge: {edge_version.data if edge_version else 'None'}")

