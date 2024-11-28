from django.db import models
from django.utils.timezone import now

class Tree(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return self.name

    def create_tag(self, name, description=None, version=None):
        if version and hasattr(version, 'tag'):
            raise ValueError("This version already has a tag associated with it.")

        # If no version is provided, create a new TreeVersion without a tag initially
        if not version:
            version = TreeVersion.objects.create(tree=self)

        # Create the tag and associate it with the tree
        tag = Tag.objects.create(tree=self, name=name, description=description, version=version)

        # Update the TreeVersion to link it back to the tag
        version.tag = tag
        version.save()

        self._snapshot_current_state(version)

        return tag

    def _duplicate_version_data(self, source_version, target_version):
        # Duplicate node versions
        for node_version in source_version.node_versions.all():
            TreeNodeVersion.objects.create(
                node=node_version.node,
                version=target_version,
                data=node_version.data
            )
        # Duplicate edge versions
        for edge_version in source_version.edge_versions.all():
            TreeEdgeVersion.objects.create(
                edge=edge_version.edge,
                version=target_version,
                data=edge_version.data
            )

    def _snapshot_current_state(self, version):
        # Snapshot all current nodes
        for node in self.nodes.all():
            TreeNodeVersion.objects.create(
                node=node,
                version=version,
                data=node.data
            )

        # Snapshot all current edges
        for edge in TreeEdge.objects.filter(
            incoming_node__tree=self,
            outgoing_node__tree=self
        ):
            TreeEdgeVersion.objects.create(
                edge=edge,
                version=version,
                data=edge.data
            )

    def create_new_tree_version_from_tag(self, tag_name):
        # Retrieve the tagged version
        try:
            tag = self.tags.get(name=tag_name)
            base_version = self.versions.get(tag=tag)
        except Tag.DoesNotExist:
            raise ValueError(f"Tag '{tag_name}' does not exist.")
        # Create a new version with base_version as parent
        new_version = TreeVersion.objects.create(tree=self, parent_version=base_version)
        # Duplicate data from base_version to new_version
        self._duplicate_version_data(base_version, new_version)
        return new_version
    
    def restore_from_tag(self, tag_name):
        # Retrieve the tagged version
        try:
            tag = self.tags.get(name=tag_name)
            base_version = self.versions.get(tag=tag)
        except Tag.DoesNotExist:
            raise ValueError(f"Tag '{tag_name}' does not exist.")
        except TreeVersion.DoesNotExist:
            raise ValueError(f"No version associated with tag '{tag_name}'.")

        return base_version

    @classmethod
    def get_by_tag(cls, tag_name):
        try:
            tag = Tag.objects.get(name=tag_name)
            tree = tag.tree
            version = tree.versions.get(tag=tag)
            return version
        except Tag.DoesNotExist:
            raise ValueError(f"Tag '{tag_name}' does not exist.")



class TreeNode(models.Model):
    tree = models.ForeignKey(Tree, on_delete=models.CASCADE, related_name='nodes')
    data = models.JSONField()
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"Node {self.id} in Tree {self.tree.name}"

class TreeEdge(models.Model):
    incoming_node = models.ForeignKey(TreeNode, on_delete=models.CASCADE, related_name='outgoing_edges')
    outgoing_node = models.ForeignKey(TreeNode, on_delete=models.CASCADE, related_name='incoming_edges')
    data = models.JSONField()
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"Edge {self.id} from Node {self.incoming_node.id} to Node {self.outgoing_node.id}"

class Tag(models.Model):
    tree = models.ForeignKey(Tree, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    version = models.OneToOneField(
        'TreeVersion',
        on_delete=models.CASCADE,
        related_name='tag'
    )
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"Tag {self.name} for Tree {self.tree.name}"

class TreeVersion(models.Model):
    tree = models.ForeignKey(Tree, on_delete=models.CASCADE, related_name='versions')
    parent_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='child_versions'
    )
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        if hasattr(self, 'tag'):  # Check if a tag exists
            return f"Version {self.id} (Tag: {self.tag.name}) of Tree {self.tree.name}"
        return f"Version {self.id} of Tree {self.tree.name}"
    
    def add_node(self, data):
        # Create a new node associated with the tree and pass the data
        node = TreeNode.objects.create(tree=self.tree, data=data)
        # Create a node version for this version
        node_version = TreeNodeVersion.objects.create(
            node=node,
            version=self,
            data=data
        )
        return node_version

    def add_existing_node(self, node, data):
        # Create a node version for an existing node
        node_version = TreeNodeVersion.objects.create(
            node=node,
            version=self,
            data=data
        )
        return node_version
    
    def add_edge(self, incoming_node_id, outgoing_node_id, data):
        # Retrieve the incoming and outgoing nodes
        try:
            incoming_node = self.tree.nodes.get(id=incoming_node_id)
            outgoing_node = self.tree.nodes.get(id=outgoing_node_id)
        except TreeNode.DoesNotExist:
            raise ValueError("One or both of the nodes do not exist in this tree.")

        # Create a new edge and pass the data
        edge = TreeEdge.objects.create(
            incoming_node=incoming_node,
            outgoing_node=outgoing_node,
            data=data  # Pass the required data here
        )

        # Create an edge version for this version
        edge_version = TreeEdgeVersion.objects.create(
            edge=edge,
            version=self,
            data=data
        )
        return edge_version

    def add_existing_edge(self, edge, data):
        # Create an edge version for an existing edge
        edge_version = TreeEdgeVersion.objects.create(
            edge=edge,
            version=self,
            data=data
        )
        return edge_version

    def get_root_nodes(self):
        # Root nodes are those with no incoming edges in this version
        node_ids_with_incoming_edges = self.edge_versions.values_list('edge__outgoing_node_id', flat=True)
        root_node_versions = self.node_versions.exclude(node__id__in=node_ids_with_incoming_edges)
        return root_node_versions

    def get_node(self, node_id):
        try:
            node_version = self.node_versions.get(node__id=node_id)
            return node_version
        except TreeNodeVersion.DoesNotExist:
            raise ValueError(f"Node with id {node_id} does not exist in this version.")

    def get_child_nodes(self, node_id):
        outgoing_edges = self.edge_versions.filter(edge__incoming_node__id=node_id)
        child_node_ids = outgoing_edges.values_list('edge__outgoing_node__id', flat=True)
        child_nodes = self.node_versions.filter(node__id__in=child_node_ids)
        return child_nodes

    def get_parent_nodes(self, node_id):
        incoming_edges = self.edge_versions.filter(edge__outgoing_node__id=node_id)
        parent_node_ids = incoming_edges.values_list('edge__incoming_node__id', flat=True)
        parent_nodes = self.node_versions.filter(node__id__in=parent_node_ids)
        return parent_nodes
    
    def get_node_edges(self, node_id):
        node_edges = self.edge_versions.filter(
            models.Q(edge__incoming_node__id=node_id) | models.Q(edge__outgoing_node__id=node_id)
        )
        return node_edges

    def traverse_tree(self, node_id, visited=None):
        if visited is None:
            visited = set()
        if node_id in visited:
            return
        visited.add(node_id)
        node = self.get_node(node_id)
        print(f"Node {node_id} metadata: {node.data}")
        edges = self.get_node_edges(node_id)
        for edge_version in edges:
            edge = edge_version.edge
            outgoing_node_id = edge.outgoing_node.id if edge.incoming_node.id == node_id else None
            if outgoing_node_id and outgoing_node_id not in visited:
                self.traverse_tree(outgoing_node_id, visited)

    def get_nodes_at_depth(self, depth):
        from collections import deque

        root_nodes = self.get_root_nodes()
        nodes_at_depth = []
        queue = deque([(node.node.id, 0) for node in root_nodes])

        while queue:
            current_node_id, current_depth = queue.popleft()
            if current_depth == depth:
                node_version = self.get_node(current_node_id)
                nodes_at_depth.append(node_version)
            elif current_depth < depth:
                child_nodes = self.get_child_nodes(current_node_id)
                for child in child_nodes:
                    queue.append((child.node.id, current_depth + 1))
        return nodes_at_depth

    def find_path(self, start_node_id, end_node_id):
        from collections import deque

        queue = deque()
        queue.append((start_node_id, []))
        visited = set()

        while queue:
            current_node_id, path = queue.popleft()
            if current_node_id == end_node_id:
                # Return the path along with the edges
                return path + [(current_node_id, None)]
            if current_node_id in visited:
                continue
            visited.add(current_node_id)
            edges = self.edge_versions.filter(edge__incoming_node__id=current_node_id)
            for edge_version in edges:
                edge = edge_version.edge
                next_node_id = edge.outgoing_node.id
                queue.append((next_node_id, path + [(current_node_id, edge_version)]))
        return None


class TreeNodeVersion(models.Model):
    node = models.ForeignKey(TreeNode, on_delete=models.CASCADE, related_name='versions')
    version = models.ForeignKey(TreeVersion, on_delete=models.CASCADE, related_name='node_versions')
    data = models.JSONField()
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"NodeVersion {self.id} for Node {self.node.id} in Version {self.version.id}"

class TreeEdgeVersion(models.Model):
    edge = models.ForeignKey(TreeEdge, on_delete=models.CASCADE, related_name='versions')
    version = models.ForeignKey(TreeVersion, on_delete=models.CASCADE, related_name='edge_versions')
    data = models.JSONField()
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"EdgeVersion {self.id} for Edge {self.edge.id} in Version {self.version.id}"
