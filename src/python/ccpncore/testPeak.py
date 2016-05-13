
class propertyList(list):
    """class to wrap a property if this is a list which needs updating in the api
    Using a list for now to store my values, but obviously that would be the api in 'real' life
    """
    
    def __init__(self, parent, apiName):
        list.__init__(self)
        self.parent = parent
        self.apiName = apiName
        
#    def __len__(self):
#        return len(self.parent._wrappedData.sortedPeakDims())
        
    def __getitem__(self, index):
        if index >= len(self):
            raise IndexError
            return
        #get values from api
        print('getting item %d: using "%s" from _wrappedData' % (index,self.apiName))
        #x = self.parent._wrappedData.sortedPeakDims()[index]
        #return getattr(x, self.apiName)
        return list.__getitem__(self, index)
        
    def __setitem__(self, index, value):
        if index >= len(self):
            raise IndexError
            return
        #update the api value
        print('setting item %d to %s: using "%s" in _wrappedData' % (index, value, self.apiName))
        #x = self.parent._wrappedData.sortedPeakDims()[index]
        #setattr(x, self.apiName, value)
        list.__setitem__(self,index, value)

    def __iter__(self):
        #values = [getattr(x, self.apiName) for x in self.parent._wrappedData.sortedPeakDims()]
        #return list.__iter__(valuesist)
        return list.__iter__(self)


class myPeak():

    def __init__(self, *positions):
        
        # define a propertyList for the positions attribute of the Peak instance
        self._positions = propertyList(self, "value")  # in api it is called value
        
        # give it some values for now
        for p in positions:
            self._positions.append(p)
    
    @property
    def positions(self):
        return self._positions
    
    @positions.setter
    def positions(self, value):
        self._positions = value
    
    def __str__(self):
        return str(self._positions)


### testing
if __name__ == '__main__':
    p = myPeak(1,2,3)
    print(p)
    p.positions[1] = 10
    print(p.positions)
    print(p.positions[0])
    p.positions[5] = 50