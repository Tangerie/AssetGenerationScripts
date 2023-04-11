import inspect

current_indent = 0
INDENT_SIZE = 2

def reset():
    global current_indent
    current_indent = 0

def indent():
    global current_indent
    current_indent += 1

def undent():
    global current_indent
    current_indent -= 1

def log(*data):
    print(f"{current_indent * INDENT_SIZE * ' '}{' '.join([str(x) for x in data])}")

def header(data):
    log(f"> {data}")
    indent()

def debug_members(obj):
    for x, _ in inspect.getmembers(obj):
        log(x)

def debug_object_properties(obj):
    log(obj)
    for prop in obj.properties():
        log(f"{prop} = {getattr(obj, prop)}")

def debug_widget(obj):
    if obj is None: return
    header(f"{obj.get_name()} [{obj.get_class()}]")
    props = obj.properties()

    # for prop in props:
    #     print(f"{prop} = {getattr(obj, prop)}") 

    if "WidgetTree" in props and obj.WidgetTree is not None:
        debug_widget(obj.WidgetTree)

    if "RootWidget" in props and obj.RootWidget is not None:
        debug_widget(obj.RootWidget)

    if "Content" in props and obj.Content is not None:
        debug_widget(obj.Content)

    if "Slots" in props and obj.Slots is not None:
        for s in obj.Slots:
            debug_widget(s)

    undent()
    