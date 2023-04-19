'''
import unreal_engine as ue
ue.py_exec("Testing/StructTest.py")
'''

import importlib

import Tools.FModel
importlib.reload(Tools.FModel)


JSON_PATH = r"F:\FModel\Output\Exports\Phoenix\Content\Gameplay\ToolSet\Items\Wand\BP_WandTool.json"

fmodel = Tools.FModel.FModelJson(JSON_PATH)

