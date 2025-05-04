import pytest

def test_basic_functionality():
    """A simple test that should always pass"""
    assert 1 + 1 == 2
    
def test_string_operations():
    """Test basic string operations"""
    assert "hello" + " world" == "hello world"
    assert "hello".upper() == "HELLO"
    
class TestBasicClass:
    """A test class with multiple test methods"""
    
    def test_list_operations(self):
        """Test basic list operations"""
        my_list = [1, 2, 3]
        my_list.append(4)
        assert len(my_list) == 4
        assert my_list[3] == 4
        
    def test_dict_operations(self):
        """Test basic dictionary operations"""
        my_dict = {"a": 1, "b": 2}
        my_dict["c"] = 3
        assert len(my_dict) == 3
        assert my_dict["c"] == 3 