from krita import *
import ast



def getNodes(node, rsltArr):
    for i in node.childNodes():
        getNodes(i, rsltArr)
    rsltArr.append(node)

def getTagsFromLayerName(name):
    ret = {}
    markerIdx = name.find("#")
    if markerIdx != -1:
        statements = ast.parse(name[markerIdx + 1:]).body
        for i in statements:
            if type(i.value) == ast.Num:
                ret[i.targets[0].id] = i.value.n
            elif type(i.value) == ast.Str:
                ret[i.targets[0].id] = i.value.s
            else:
                raise Exception("Only Num and Str are available:" + type(i.value))
    return ret

def dicCombiGen(d):
    keys = [x for x in d]
    indices = [0 for x in keys]

    while True:
        ret = {}
        for i in range(len(keys)):
            key = keys[i]
            index = indices[i]
            ret[key] = d[key][index]
        yield ret

        curIdx = 0
        done = False
        while (not done) and (curIdx < len(indices)):
            indices[curIdx] += 1
            if len(d[keys[curIdx]]) == indices[curIdx]:
                indices[curIdx] = 0
                curIdx += 1
            else:
                done = True

        # done is False until all of the combinations are generated
        if not done:
            break

def getDictStr(d):
    ret = "_"
    for i in d:
        ret += i + str(d[i]) + "_"

    return ret[:-1]

def isVisibleFromTagState(myNodeTags, curDic):
    for i in myNodeTags:
        if i in curDic and curDic[i] != myNodeTags[i]:
            return False
    return True

class MyNode:
    def __init__(self, node):
        self.node = node
        self.tags = getTagsFromLayerName(node.name())

class MyCreateDiffs:
    def __init__(self):
        self.prevBatch = Krita.instance().batchmode()
        self.doc = Krita.instance().activeDocument()
        self.root = self.doc.rootNode()

        tmpnodes = []
        getNodes(self.root, tmpnodes)
        self.nodes = [MyNode(x) for x in tmpnodes]

        self.tags = {}
        for i in self.nodes:
            for j in i.tags:
                if j in self.tags:
                    # add only a new value. skip existing values.
                    if not i.tags[j] in self.tags[j]:
                        self.tags[j].append(i.tags[j])
                else:
                    self.tags[j] = [i.tags[j]]

        self.exporter = self.defaultCreateDiffMethod

    def setExporter(self, method):
        self.exporter = method

    def defaultCreateDiffMethod(self):
        Krita.instance().setBatchmode(True)

        info = InfoObject()
        info.setProperty("alpha", True)
        info.setProperty("compression", 1)
        info.setProperty("forceSRGB", False)
        info.setProperty("indexed", False)
        info.setProperty("interlaced", False)
        info.setProperty("saveSRGBProfile", False)
        info.setProperty("transparencyFillcolor", [0, 0, 0])# this doesnt work?

        for i in dicCombiGen(self.tags):
            # you can skip some elements by your own filter.
            if False:
                continue

            for j in self.nodes:
                if len(j.tags) == 0:
                    continue
                visible = isVisibleFromTagState(j.tags, i)
                j.node.setVisible(visible)

            self.doc.refreshProjection()

            # export png, 
            # for now, a pop up is shown for every export even when batchmode is set to True.
            # there must be something important i don't know. fix it later.
            path = "nowTesting" + getDictStr(i) + ".png"
            if self.doc.exportImage(path, info):
                print("file created:" + path)
            else:
                print("export failed:" + path)

        Krita.instance().setBatchmode(self.prevBatch)

    def export(self):
        visibleArr = [x.node.visible() for x in self.nodes]

        self.exporter()

        for i in range(len(self.nodes)):
            flag = visibleArr[i]
            self.nodes[i].node.setVisible(flag)
        self.doc.refreshProjection()

if __name__ == '__main__':
    obj = MyCreateDiffs()
    obj.export()

