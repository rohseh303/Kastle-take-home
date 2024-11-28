from django.test import TestCase
from tree_manager.models import (
    Tree,
    TreeNode,
    TreeEdge,
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

        tag = self.tree.create_tag(
            name="release-v1.1",
            description="Added new setting",
            version=modified_version
        )

class FeatureBranchingTestCase(TestCase):
    def setUp(self):
        # Create a tree and tag main version
        self.tree = Tree.objects.create(name="Main Tree")
        self.node_main = TreeNode.objects.create(tree=self.tree, data={"main": True})

        # Creating and tagging the main version
        self.tree.create_tag(name="main-v2.0", description="Main version 2.0")

    def test_feature_branching(self):
        # Creating a feature branch from the main version
        feature_branch = self.tree.create_new_tree_version_from_tag("main-v2.0")
        self.assertIsNotNone(feature_branch)

        # Making feature-specific changes
        node1 = feature_branch.add_node(data={"feature_flag": True})
        node2 = feature_branch.add_node(data={"config": "new_setting"})
        self.assertIsNotNone(node1)
        self.assertIsNotNone(node2)

        # Adding an edge between the new nodes
        edge_version = feature_branch.add_edge(
            incoming_node_id=node1.node.id,
            outgoing_node_id=node2.node.id,
            data={"relation": "depends_on"}
        )
        self.assertIsNotNone(edge_version)
        self.assertEqual(edge_version.data, {"relation": "depends_on"})

        # Tagging the feature branch
        feature_branch_tag = self.tree.create_tag(
            name="feature-x-v1",
            description="Feature X implementation",
            version=feature_branch
        )
        self.assertEqual(feature_branch_tag.name, "feature-x-v1")

        # Verify that the tag is associated with the feature branch version
        self.assertEqual(feature_branch.tag.name, "feature-x-v1")

class RollbackScenarioTestCase(TestCase):
    def setUp(self):
        # Create a tree and tag a stable version
        self.tree = Tree.objects.create(name="Stable Tree")
        self.node_stable = TreeNode.objects.create(tree=self.tree, data={"stable": True})

        # Tag the stable version (TreeVersion is created automatically)
        self.tree.create_tag(name="stable-v1", description="Stable version")

    def test_rollback_scenario(self):
        # Making potentially risky changes in a new version
        modified_version = self.tree.create_new_tree_version_from_tag("stable-v1")
        self.assertIsNotNone(modified_version)

        # Add a new experimental node to the modified version
        new_node_version = modified_version.add_node(data={"experimental": True})
        self.assertIsNotNone(new_node_version)

        # Add an edge connecting the stable node to the experimental node
        edge_version = modified_version.add_edge(
            incoming_node_id=self.node_stable.id,
            outgoing_node_id=new_node_version.node.id,
            data={"type": "experimental"}
        )
        self.assertIsNotNone(edge_version)

        # Simulate problem detection
        problems_detected = True

        if problems_detected:
            # Instead of modifying the live tree, use the base_version
            rollback_version = self.tree.get_by_tag("stable-v1")
            self.assertIsNotNone(rollback_version)

            # Verify that the experimental node is not present in the rollback version
            with self.assertRaises(ValueError):
                rollback_version.get_node(new_node_version.node.id)


class TreeFetchingByTagTestCase(TestCase):
    def setUp(self):
        # Create a tree and nodes in the live tree
        self.tree = Tree.objects.create(name="Historical Tree")
        self.node1 = TreeNode.objects.create(tree=self.tree, data={"value": 1})
        self.node2 = TreeNode.objects.create(tree=self.tree, data={"value": 2})
        self.node3 = TreeNode.objects.create(tree=self.tree, data={"value": 3})
        self.node4 = TreeNode.objects.create(tree=self.tree, data={"value": 4})
        self.node5 = TreeNode.objects.create(tree=self.tree, data={"value": 5})

        # Tag the current state (nodes will be snapshotted)
        self.tree.create_tag(name="release-v1.0", description="Release version 1.0")

        # Add edges to the current version
        current_version = self.tree.versions.first()
        self.edge1 = current_version.add_edge(
            incoming_node_id=self.node1.id,
            outgoing_node_id=self.node2.id,
            data={"relation": "child"}
        )
        self.edge2 = current_version.add_edge(
            incoming_node_id=self.node2.id,
            outgoing_node_id=self.node3.id,
            data={"relation": "child"}
        )
        self.edge3 = current_version.add_edge(
            incoming_node_id=self.node2.id,
            outgoing_node_id=self.node4.id,
            data={"relation": "child"}
        )
        self.edge4 = current_version.add_edge(
            incoming_node_id=self.node4.id,
            outgoing_node_id=self.node5.id,
            data={"relation": "child"}
        )

    def test_tree_fetching_by_tag(self):
        # Get the tree version by tag
        historical_version = self.tree.get_by_tag("release-v1.0")
        self.assertEqual(historical_version.tag.name, "release-v1.0")

        # Get the root node(s)
        root_nodes = historical_version.get_root_nodes()
        self.assertEqual(len(root_nodes), 1)
        root_node = root_nodes[0]
        self.assertEqual(root_node.node.id, self.node1.id)

        # Traverse from a specific node
        node = historical_version.get_node(node_id=self.node1.id)
        self.assertIsNotNone(node)
        self.assertEqual(node.node.id, self.node1.id)

        children = historical_version.get_child_nodes(node_id=self.node1.id)
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].node.id, self.node2.id)

        parents = historical_version.get_parent_nodes(node_id=self.node3.id)
        self.assertEqual(len(parents), 1)
        self.assertEqual(parents[0].node.id, self.node2.id)

        # Get edge information
        edges = historical_version.get_node_edges(node_id=self.node2.id)
        self.assertEqual(len(edges), 3)  # 1 incoming, 2 outgoing

        # for edge_version in edges:
        #     edge = edge_version.edge
        #     connected_node_id = (
        #         edge.outgoing_node.id if edge.incoming_node.id == self.node2.id else edge.incoming_node.id
        #     )
        #     print(f"Edge {edge_version.id} metadata: {edge_version.data}")
        #     print(f"Connected to node: {connected_node_id}")

        for edge_version in edges:
            edge = edge_version.edge

            # Determine the connected node and the relationship direction
            if edge.incoming_node.id == self.node2.id:
                connected_node_id = edge.outgoing_node.id
                relationship = "child (outgoing)"
            else:
                connected_node_id = edge.incoming_node.id
                relationship = "parent (incoming)"

            # Print edge metadata and the connected node with its relationship
            print(f"Edge {edge_version.id} metadata: {edge_version.data}")
            print(f"Connected to node: {connected_node_id} as {relationship}")

        # Traverse entire tree structure
        print("\n\nTraversing the tree:")
        def traverse_tree(version, node_id, visited=None):
            if visited is None:
                visited = set()
            if node_id in visited:
                return
            visited.add(node_id)
            node_version = version.get_node(node_id)
            print(f"Node {node_id} metadata: {node_version.data}")
            edges = version.get_node_edges(node_id)
            for edge_version in edges:
                edge = edge_version.edge
                if edge.incoming_node.id == node_id:
                    next_node_id = edge.outgoing_node.id
                    if next_node_id not in visited:
                        print(f"Edge metadata: {edge_version.data}")
                        traverse_tree(version, next_node_id, visited)

        # Start traversal from root
        for root in historical_version.get_root_nodes():
            traverse_tree(historical_version, root.node.id)

        # Get all nodes at a specific depth
        level_2_nodes = historical_version.get_nodes_at_depth(2)
        level_2_node_ids = [nv.node.id for nv in level_2_nodes]
        print(f"\n\nNodes at depth 2: {level_2_node_ids}")
        self.assertIn(self.node3.id, level_2_node_ids)
        self.assertIn(self.node4.id, level_2_node_ids)

        # Find path between nodes
        path = historical_version.find_path(start_node_id=self.node1.id, end_node_id=self.node5.id)
        self.assertIsNotNone(path)
        expected_path = [self.node1.id, self.node2.id, self.node4.id, self.node5.id]
        print(f"\n\nExpected path: {expected_path} between {self.node1.id} and {self.node5.id}")
        actual_path = [node_id for node_id, _ in path]
        self.assertEqual(actual_path, expected_path)

        for node_id, edge_version in path:
            node_version = historical_version.get_node(node_id)
            print(f"Node: {node_version.data}")
            if edge_version:
                print(f"Connected by edge: {edge_version.data if edge_version else 'None'}")

class NodeAndEdgeMetadataVersioningTestCase(TestCase):
    def setUp(self):
        # Create a tree and initial nodes
        self.tree = Tree.objects.create(name="Metadata Test Tree")
        self.node1 = TreeNode.objects.create(tree=self.tree, data={"name": "Node1", "value": 1})
        self.node2 = TreeNode.objects.create(tree=self.tree, data={"name": "Node2", "value": 2})

        # Add an edge between nodes
        self.edge = TreeEdge.objects.create(
            incoming_node=self.node1,
            outgoing_node=self.node2,
            data={"relation": "child"}
        )

        # Tag the current state
        self.tree.create_tag(name="initial", description="Initial version snapshot")

    def test_metadata_versioning_with_rollback(self):
        # Retrieve the initial version
        initial_version = self.tree.get_by_tag("initial")
        initial_node1 = initial_version.get_node(self.node1.id)
        initial_node2 = initial_version.get_node(self.node2.id)
        initial_edge = initial_version.get_node_edges(self.node1.id)[0]

        # Validate metadata in the initial version
        self.assertEqual(initial_node1.data, {"name": "Node1", "value": 1})
        self.assertEqual(initial_node2.data, {"name": "Node2", "value": 2})
        self.assertEqual(initial_edge.data, {"relation": "child"})

        # Modify the live tree (simulate new changes)
        self.node1.data = {"name": "Node1", "value": 42}  # Change metadata
        self.node1.save()
        self.edge.data = {"relation": "updated-child"}  # Change edge metadata
        self.edge.save()

        # Validate the version still reflects the original metadata
        self.assertEqual(initial_node1.data, {"name": "Node1", "value": 1})  # Should not change
        self.assertEqual(initial_edge.data, {"relation": "child"})  # Should not change

        # Create a new version
        self.tree.create_tag(name="updated", description="Updated tree snapshot")
        updated_version = self.tree.get_by_tag("updated")
        updated_node1 = updated_version.get_node(self.node1.id)
        updated_edge = updated_version.get_node_edges(self.node1.id)[0]

        # Validate that the updated version reflects the new metadata
        self.assertEqual(updated_node1.data, {"name": "Node1", "value": 42})
        self.assertEqual(updated_edge.data, {"relation": "updated-child"})

        # Rollback to the initial version
        rolled_back_version = self.tree.restore_from_tag("initial")
        rolled_back_node1 = rolled_back_version.get_node(self.node1.id)
        rolled_back_node2 = rolled_back_version.get_node(self.node2.id)
        rolled_back_edge = rolled_back_version.get_node_edges(self.node1.id)[0]

        # Validate the tree structure and metadata after rollback
        self.assertEqual(rolled_back_node1.data, {"name": "Node1", "value": 1})
        self.assertEqual(rolled_back_node2.data, {"name": "Node2", "value": 2})
        self.assertEqual(rolled_back_edge.data, {"relation": "child"})

        # Ensure changes made in the updated version do not exist in the rolled-back version
        with self.assertRaises(ValueError):
            rolled_back_version.get_node(self.node2.id + 1)  # Assuming no additional nodes exist
