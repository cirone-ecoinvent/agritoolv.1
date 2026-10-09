class NonStrictInputMapping(object):
    def __init__(self, originalInputs, mappingRules):
        self.originalInputs = originalInputs
        self._mappingRules = mappingRules
        
    def __getattr__(self, name):
        return self._mappingRules.get(name, IDENTITY_INPUT_MAPPING_RULE).mapField(name, self)
    
    def __getitem__(self, name):
        return self.__getattr__(name)
    
    def __contains__(self, name):
        return name in self._mappingRules or name in self.originalInputs
    
class InputMappingRule(object):
    def mapField(self, attrName, mapping):
        raise "Please override this method"
    
class IdentityInputMappingRule(InputMappingRule):
    def mapField(self, attrName, mapping):
        return mapping.originalInputs[attrName]
    
IDENTITY_INPUT_MAPPING_RULE = IdentityInputMappingRule()
    
class SimpleInputMappingRule(InputMappingRule):
    def __init__(self, otherParam):
        self._otherParam = otherParam
        
    def mapField(self, attrName, mapping):
        return mapping.originalInputs[self._otherParam]
    
class InputAsEnumMappingRule(InputMappingRule):
    def __init__(self, paramName, enumClass):
        self._paramName = paramName
        self._enumClass = enumClass
        
    def mapField(self, attrName, mapping):
        return self._enumClass(mapping.originalInputs[self._paramName])
    
class MapMappingRule(InputMappingRule):
    def __init__(self, enumToFieldDict):
        self._enumToFieldDict = enumToFieldDict
    
    def mapField(self, attrName, mapping):
        hasonevalue = False
        res = {}
        for k,v in self._enumToFieldDict.items():
            try:
                res[k] = mapping.originalInputs[v]
                hasonevalue = True
            except KeyError:
                res[k] = 0.0
        if hasonevalue:
            return res
        else:
            raise KeyError
