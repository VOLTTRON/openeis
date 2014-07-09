class Report:
    
    def __init__(self, description):
        self.description = description
        self.elements = []
        
    def add_element(self, element):
        if isinstance(element, ReportElement) is False:
            raise ValueError('Can only add ReportElement to Report')
        self.elements.append(element)
    
    def __str__(self):
        str = 'Report: '
        str += self.description + '\n'
        str += 'Report Elements: \n'
        for element in self.elements:
             str += element.__str__()
             str += '\n'
        return str

class ReportElement:
    
    def __init__(self, title=None, desc=None):
        self.title = title
        self.desc = desc
    
    def __str__(self):
        members = dir(self)
        result = self.__class__.__name__ + ': '
        for key in members:
            if key.startswith("_") or callable(getattr(self,key)) is True:
                continue
            value = getattr(self,key)
            if value is not None:
                result += '\n\t' + key + ' = ' + str(value) + ', '
        return result
    
class TextBlurb(ReportElement):
    
    def __init__(self, text):
        self.text = text
            
class Table(ReportElement):
    
    def __init__(self, table_name):
        self.table_name = table_name

class XYDataSet():
    
    def __init__(self, table_name, x_column, y_column):
        self.table_name = table_name
        self.x_column = x_column
        self.y_column = y_column
        
    def __repr__(self):
        members = dir(self)
        result = self.__class__.__name__ + '('
        result += self.table_name + ','
        result += self.x_column + ','
        result += self.y_column + ')'
        return result
    

    
            
class XYPlot(ReportElement):
    
    def __init__(self, xy_dataset_list, x_label, y_label, title=None, desc=None):
        super(XYPlot, self).__init__(title, desc)
        self.xy_dataset_list = xy_dataset_list
        self.x_label = x_label
        self.y_label = y_label


class LinePlot(XYPlot):
    pass

#TODO
class BarChart(XYPlot):
    pass

class HeatMap(XYPlot):
    pass


if __name__ == '__main__':
    
    report = Report("This is a report description")
    
    #line_plot = LinePlot(title='Title', table_name="OAT", x_column="Temperature", y_column="Timestamp")
    table = Table(table_name="XYZ")
    text_blurb = TextBlurb(text="this is a text blurb")
    
    xy_dataset_list = []
    xy_dataset_list.append(XYDataSet('OAT','Timestamp','Temperature'))
    xy_dataset_list.append(XYDataSet('Sensor','Timestamp','SensorValue'))
    xy_plot = LinePlot(xy_dataset_list, title='line chart', x_label='Temperature', y_label='values')
    
    report.add_element(table)
    report.add_element(text_blurb)
    report.add_element(xy_plot)
    
    print(report)
