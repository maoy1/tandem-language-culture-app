"""Local XPath 1.0 transport support; no tenant certification or runtime use."""
from lxml import etree


def xml(value):
    if isinstance(value,str):return etree.fromstring(value.encode())
    assert isinstance(value,dict) and len(value)==1, 'JSON XML requires one root'
    def add(parent,name,child):
        if isinstance(child,list):
            for item in child:add(parent,name,item)
            return
        node=etree.SubElement(parent,name)
        if isinstance(child,dict):
            for key,item in child.items():add(node,key,item)
        elif child is not None:node.text=str(child).lower() if isinstance(child,bool) else str(child)
    name,content=next(iter(value.items()));root=etree.Element(name)
    if isinstance(content,dict):
        for key,item in content.items():add(root,key,item)
    elif content is not None:root.text=str(content)
    return root


def xpath(root,expression):
    return root.xpath(expression)
