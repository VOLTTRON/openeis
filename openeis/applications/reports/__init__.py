'''Report meta data objects for applications to describe output for user presentation.'''

class Report:
    
    def __init__(self, description):
        self.description = description
        self.elements = []
        
    def add_element(self, element):
        if isinstance(element, ReportElement) is False:
            raise ValueError('Can only add ReportElement to Report')
        self.elements.append(element)
    
    def __str__(self):
        results = 'Report: '
        results += self.description + '\n'
        results += 'Report Elements: \n'
        for element in self.elements:
            results += str(element)
            results += '\n'
        return results

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
                result += '\n\t' + key + ' = ' + str(value)
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

class BarChart(XYPlot):
    pass

class ScatterPlot(XYPlot):
    pass

class HeatMap(ReportElement):
    
    def __init__(self, table_name, x_column, y_column, z_column, x_label=None, y_label=None, z_label=None, title=None, desc=None):
        super(HeatMap, self).__init__(title, desc)
        self.table_name = table_name
        self.x_column  = x_column
        self.y_column = y_column
        self.z_column = z_column
        self.x_label = x_label
        self.y_label = y_label
        self.z_label = z_label


if __name__ == '__main__':
    
    report = Report("This is a report description")
    
    table = Table(table_name="XYZ")
    report.add_element(table)
    
    text_blurb = TextBlurb(text="this is a text blurb")
    report.add_element(text_blurb)
    
    xy_dataset_list = []
    xy_dataset_list.append(XYDataSet('OAT','Timestamp','Temperature'))
    xy_dataset_list.append(XYDataSet('Sensor','Timestamp','SensorValue'))
    line_plot = LinePlot(xy_dataset_list, title='line chart', x_label='Temperature', y_label='values')
    report.add_element(line_plot)
    
    bar_chart = BarChart(xy_dataset_list, title='bar chart', x_label='Temperature', y_label='values')
    report.add_element(bar_chart)
    
    scatter_plot = ScatterPlot(xy_dataset_list, title='scatter plot', x_label='Temperature', y_label='values')
    report.add_element(scatter_plot)
    
    heat_map = HeatMap(table_name='OAT_HeatMap', x_column='HourOfDay', y_column='Date', z_column='Temperature')
    report.add_element(heat_map)
    
    print(report)
