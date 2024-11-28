from django.contrib import admin
from .models import Tree, TreeNode, TreeEdge, Tag, TreeVersion, TreeNodeVersion, TreeEdgeVersion

admin.site.register(Tree)
admin.site.register(TreeNode)
admin.site.register(TreeEdge)
admin.site.register(Tag)
admin.site.register(TreeVersion)
admin.site.register(TreeNodeVersion)
admin.site.register(TreeEdgeVersion)
