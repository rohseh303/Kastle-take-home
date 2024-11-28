from django.test import TestCase
from tree_manager.models import Tree, TreeNode, TreeEdge, Tag, TreeVersion

class ConfigurationManagementTestCase(TestCase):
    def setUp(self):
        self.tree = Tree.objects.create(name="Configuration Tree")

    def test_configuration_management(self):
        # Creating a new configuration version
        new_tag = self.tree.create_tag("release-v1.0", description="Initial stable release")

        # Making changes to the configuration
        modified_tree_version = self.tree.create_new_tree_version_from_tag("release-v1.0")
        new_node_version = modified_tree_version.add_node(data={"setting": "new_value"})

        # Adding an edge between nodes
        modified_tree_version.add_edge(
            incoming_node_id=self.tree.nodes.first().id,
            outgoing_node_id=new_node_version.node.id,
            data={"weight": 0.5}
        )

        # Creating a new tag after modifications
        modified_tree_version.tag = self.tree.tags.create(
            name="release-v1.1",
            description="Added new setting"
        )
        modified_tree_version.save()

        # Assertions
        self.assertTrue(self.tree.tags.filter(name="release-v1.1").exists())
        self.assertEqual(modified_tree_version.tag.name, "release-v1.1")