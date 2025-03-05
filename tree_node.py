class TreeNode:
    def __init__(self, byte_value):
        """Initialize a tree node with a byte value and empty children.
        
        Args:
            byte_value (str): Binary string representation (e.g., "11100000")
        """
        self.byte = byte_value
        self.children = [None] * 8  # 8 bits = 8 possible children
        self.value = None  # For leaf nodes storing actual data

    def set_child(self, index, child):
        """Set a child node at the specified index.
        
        Args:
            index (int): Index in the children array (0-7)
            child (TreeNode or str): Child node or value to set
        """
        if 0 <= index < 8:  # Validate index
            self.children[index] = child

    def get_child(self, index):
        """Get the child node at the specified index.
        
        Args:
            index (int): Index in the children array (0-7)
        
        Returns:
            TreeNode or str or None: Child node, value, or None if invalid index
        """
        if 0 <= index < 8:  # Validate index
            return self.children[index]
        return None

    def set_value(self, value):
        """Set the value for a leaf node.
        
        Args:
            value (str): Value to store in the leaf node
        """
        self.value = value
        self.children = None  # Clear children when setting a value

    def is_leaf(self):
        """Check if the node is a leaf node (has a value).
        
        Returns:
            bool: True if node has a value, False otherwise
        """
        return self.value is not None

    def __str__(self):
        """String representation of the node.
        
        Returns:
            str: Node information
        """
        if self.is_leaf():
            return f"Leaf Node(value='{self.value}')"
        return f"Node(byte='{self.byte}')" 