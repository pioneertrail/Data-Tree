from tree_node import TreeNode

def test_tree_node():
    # Create a root node
    root = TreeNode("11000000")
    print("Created root node with byte:", root.byte)
    
    # Test setting and getting children
    child1 = TreeNode("10000000")
    root.set_child(0, child1)
    retrieved_child = root.get_child(0)
    print("Set child at index 0, retrieved same child:", retrieved_child == child1)
    
    # Test invalid index
    root.set_child(8, TreeNode("00000000"))
    print("Getting child at invalid index returns None:", root.get_child(8) is None)
    
    # Test leaf node
    leaf = TreeNode("00000000")
    leaf.set_value("test value")
    print("Leaf node has value:", leaf.value)
    print("Is leaf node:", leaf.is_leaf())
    print("Leaf node children cleared:", leaf.children is None)

if __name__ == "__main__":
    test_tree_node() 