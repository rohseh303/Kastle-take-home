Tree Versioning System
======================

Overview
--------

The Tree Versioning System is designed to manage hierarchical tree structures stored in a SQL database. It provides robust functionality for tagging tree configurations, creating versions, traversing tree structures, and efficiently querying historical configurations. The system is implemented in Python with Django and uses SQLite as the default database for development and testing.

* * * * *

Features
--------

### 1\. Database Implementation

-   **Models**:

    -   `Tree`: Represents a tree structure.

    -   `TreeNode`: Represents individual nodes within a tree.

    -   `TreeEdge`: Represents relationships between nodes with metadata.

    -   `Tag`: Represents tags for tree versions.

    -   `TreeVersion`: Stores historical versions of trees.

    -   `TreeNodeVersion` and `TreeEdgeVersion`: Snapshot node and edge states for each version.

-   **Migration Scripts**:

    -   All necessary migrations are included for setting up the schema.

    -   Supports schema evolution with appropriate migration files.

-   **Indexes**:

    -   Indexes on foreign keys (`tree_id`, `incoming_node_id`, `outgoing_node_id`) for efficient joins.

    -   Indexes on tag names for quick lookups.

* * * * *

### 2\. Core Implementation

-   **Versioning**:

    -   Tag tree states to create immutable versions.

    -   Snapshots of nodes and edges ensure consistent historical retrieval.

-   **Tree Traversal**:

    -   Fetch root nodes, parent nodes, child nodes, and edges for a given node.

    -   Traverse the entire tree structure starting from root nodes.

    -   Fetch nodes at a specific depth.

    -   Find paths between nodes.

-   **Restoration**:

    -   Rollback to a previous tree state using tags.

-   **Integration**:

    -   Simple integration with SQLite for development.

    -   Supports scaling to other SQL databases.

* * * * *

### 3\. Tests

-   **Unit Tests**:

    -   Test individual methods for creating tags, adding nodes, and edges.

-   **Test Coverage**:

    -   Comprehensive test cases for configuration management, feature branching, and rollback scenarios.

* * * * *

### 4\. Documentation

#### Example Usage Scenarios

**1\. Configuration Management**

```
# Create a tree
tree = Tree.objects.create(name="Configuration Tree")

# Create nodes
node1 = TreeNode.objects.create(tree=tree, data={"name": "Node1"})
node2 = TreeNode.objects.create(tree=tree, data={"name": "Node2"})

# Tag the initial configuration
initial_tag = tree.create_tag(name="initial", description="Initial configuration")

# Create a new version from a tag
modified_version = tree.create_new_tree_version_from_tag("initial")
modified_version.add_node(data={"new_setting": "value"})
modified_version.add_edge(incoming_node_id=node1.id, outgoing_node_id=node2.id, data={"relation": "child"})

# Create a new tag for the modified version
modified_tag = tree.create_tag(name="release-v1.1", description="Modified configuration", version=modified_version)
```

**2\. Rollback Scenario**

```
# Restore tree state from a tag
rollback_version = tree.restore_from_tag("initial")
```

#### Installation and Setup Guide

1.  **Clone the Repository**:

    ```
    git clone https://github.com/rohseh303/Kastle-take-home.git
    cd tree_versioning
    ```

2.  **Set Up the Virtual Environment**:

    ```
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:

    ```
    pip install -r requirements.txt
    ```

4.  **Run Migrations**:

    ```
    python manage.py makemigrations
    python manage.py migrate
    ```

5.  **Run Tests**:

    ```
    python manage.py test
    ```

6.  **Start the Development Server** (optional for API testing):

    ```
    python manage.py runserver
    ```

#### Design Decisions and Tradeoffs

1.  **Tag-Version Relationship**:

    -   Implemented as a one-to-one relationship to ensure each tag uniquely identifies a version.

    -   Tradeoff: Reduces flexibility in associating multiple tags with the same version but simplifies data integrity.

2.  **Snapshot Design**:

    -   Nodes and edges are snapshotted into `TreeNodeVersion` and `TreeEdgeVersion` tables for historical consistency.

    -   Tradeoff: Requires additional storage but ensures reliable historical retrieval.

3.  **SQLite for Development**:

    -   Chosen for simplicity and portability.

    -   Tradeoff: May require adjustments for production databases like PostgreSQL or MySQL.

4.  **No UI**:

    -   Focused on backend functionality to allow easy integration with APIs or other services.

    -   Tradeoff: Users need to interact with the system programmatically or through CLI tools.

* * * * *

Future Enhancements
-------------------

-   Add API endpoints for easier integration.

-   Implement role-based access control (RBAC) for version and tag management.

-   Optimize large tree traversal with caching or advanced database queries.

-   Extend support to graph databases for complex relationships.

-   Clean up nodes and edges that are no longer in use after a rollback.

* * * * *

Contact
-------

For questions or contributions, contact rohansehgal935@gmail.com