

from .db_input import DatabaseInput
from datetime import datetime

if __name__ == '__main__':
    args = []
    
    t = {'OAT':[[{'time':datetime(200,1,1,8,0,0), 'value':50.0},
                 {'time':datetime(200,1,1,9,0,0), 'value':51.0},
                 {'time':datetime(200,1,1,10,0,0), 'value':52.0},
                 {'time':datetime(200,1,1,11,0,0), 'value':53.0},
                 {'time':datetime(200,1,1,12,0,0), 'value':54.0},
                 {'time':datetime(200,1,1,13,0,0), 'value':55.0},
                 {'time':datetime(200,1,1,14,0,0), 'value':56.0},
                 {'time':datetime(200,1,1,15,0,0), 'value':57.0},
                 {'time':datetime(200,1,1,16,0,0), 'value':58.0},
                 {'time':datetime(200,1,1,17,0,0), 'value':59.0},
                 {'time':datetime(200,1,1,18,0,0), 'value':60.0},
                ],
                [{'time':datetime(200,1,1,8,0,0), 'value':50.0},
                 {'time':datetime(200,1,1,9,0,0), 'value':50.0},
                 {'time':datetime(200,1,1,10,0,0), 'value':52.0},
                 {'time':datetime(200,1,1,11,0,0), 'value':52.0},
                 {'time':datetime(200,1,1,12,0,0), 'value':54.0},
                 {'time':datetime(200,1,1,13,0,0), 'value':54.0},
                 {'time':datetime(200,1,1,14,0,0), 'value':56.0},
                 {'time':datetime(200,1,1,15,0,0), 'value':56.0},
                 {'time':datetime(200,1,1,16,0,0), 'value':58.0},
                 {'time':datetime(200,1,1,17,0,0), 'value':58.0},
                 {'time':datetime(200,1,1,18,0,0), 'value':60.0},
                ],
                [{'time':datetime(200,1,1,8,0,0), 'value':51.0},
                 {'time':datetime(200,1,1,9,0,0), 'value':51.0},
                 {'time':datetime(200,1,1,10,0,0), 'value':53.0},
                 {'time':datetime(200,1,1,11,0,0), 'value':53.0},
                 {'time':datetime(200,1,1,12,0,0), 'value':55.0},
                 {'time':datetime(200,1,1,13,0,0), 'value':55.0},
                 {'time':datetime(200,1,1,14,0,0), 'value':57.0},
                 {'time':datetime(200,1,1,15,0,0), 'value':57.0},
                 {'time':datetime(200,1,1,16,0,0), 'value':59.0},
                 {'time':datetime(200,1,1,17,0,0), 'value':59.0},
                 {'time':datetime(200,1,1,18,0,0), 'value':60.0},
                ]]}
    
    args.append(t)
    
    t = {'Energy':[[{'time':datetime(200,1,1,8,0,0), 'value':100},
                 {'time':datetime(200,1,1,9,0,0), 'value':100},
                 {'time':datetime(200,1,1,10,0,0), 'value':100},
                 {'time':datetime(200,1,1,11,0,0), 'value':100},
                 {'time':datetime(200,1,1,12,0,0), 'value':100},
                 {'time':datetime(200,1,1,13,0,0), 'value':100},
                 {'time':datetime(200,1,1,14,0,0), 'value':100},
                 {'time':datetime(200,1,1,15,0,0), 'value':100},
                 {'time':datetime(200,1,1,16,0,0), 'value':100},
                 {'time':datetime(200,1,1,17,0,0), 'value':100},
                 {'time':datetime(200,1,1,18,0,0), 'value':100},
                ]]}
    
    args.append(t)
    
    for result in DatabaseInput.merge(*args):
        print(result)
