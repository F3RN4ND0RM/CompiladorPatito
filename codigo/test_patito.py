#!/usr/bin/env python3
"""
Test de patito.lark

Importamos nuestra gramatica
"""
from patito import patito




def test_cases():
    return [
        {
            "name" : "TC 1. Programa vacio",
            "input": "PROGRAM A ; BEGIN { } END",
            "description": "Un programa mínimo con el nombre A, sin variables ni funciones, y un bloque vacío.",
            "should_parse": True
        },
        {
            "name" : "TC 2. Programa con typo",
            "input": "PROGRAMA A ; BEGIN { } END",
            "description": "Un programa con un error tipográfico en la palabra clave 'PROGRAM', lo que debería causar un error de análisis sintáctico.",
            "should_parse": False
        },
        {
            "name" : "TC 3. Programa con VARS",
            "input": '''
                PROGRAM A ;
                VARS 
                a, b, c : INT;
                d,e,f: FLOAT;
                BEGIN { } END
            ''',
            "description": "Un programa que declara variables enteras y flotantes utilizando la sección VARS, pero sin funciones ni código en el bloque principal.",
            "should_parse": True
        },{
            "name" : "TC 4. Programa con VARS y FUNCS",
            "input": '''
                PROGRAM A ;
                VARS 
                a, b, c : INT;
                d,e,f: FLOAT;
                VOID main(aa : INT, bb: FLOAT) {                    
                    VARS
                    ab : FLOAT;
                    {                        
                        ab = aa + bb;
                    }
                };
                BEGIN { } END
            ''',
            "description": "Un programa que incluye tanto variables globales como una función principal con su propia sección de variables locales y un bloque de código que realiza una operación simple.",
            "should_parse": True
        },{
            "name" : "TC 5. Programa con FUNCS antes que VARS",
            "input": '''
                PROGRAM A ;
                VOID main(aa : INT, bb: FLOAT) {                    
                    VARS
                    ab : FLOAT;
                    {                        
                        ab = aa + bb;
                    }
                };
                VARS 
                a, b, c : INT;
                d,e,f: FLOAT;
                BEGIN { } END
            ''',
            "description": "Un programa que declara una función antes de la sección de variables globales, lo que debería causar un error de análisis sintáctico debido a la violación del orden esperado de las secciones.",
            "should_parse": False
        },{
            "name" : "TC 6. Programa con FUNCS multiples estatutos",
            "input": '''
                PROGRAM A ;
                VARS 
                a, b, c : INT;
                d,e,f: FLOAT;
                VOID main(aa : INT, bb: FLOAT) {                    
                    VARS
                    ab : FLOAT;
                    {                        
                        ab = aa + bb;
                        PRINT("a");
                    }
                    
                }; 
                                
                BEGIN { } END
            ''',
            "description": "Un programa que incluye una función principal con múltiples declaraciones y un bloque de código que realiza varias operaciones, incluyendo una asignación y una llamada a impresión.",
            "should_parse": True
        },{
            "name" : "TC 7. Programa con if y while",
            "input": '''
                PROGRAM A ;
                VARS 
                a, b, c : INT;
                d,e,f: FLOAT;
                VOID main(aa : INT, bb: FLOAT) {                    
                    VARS
                    ab : FLOAT;
                    {                        
                        ab = aa + bb;
                        PRINT("a");
                    }
                    
                }; 
                                
                BEGIN { 
                    WHILE(a > b) DO {
                        IF(a > c){
                            PRINT("a es mayor que c");
                        } ELSE {
                            PRINT("a no es mayor que c");
                        };
                    };
                } END
            ''',
            "description": "Un programa que incluye una función principal con un bloque de código que contiene una estructura de control WHILE anidada con una estructura IF-ELSE",
            "should_parse": True
        },{
            "name" : "TC 8. Programa con while roto",
            "input": '''
                PROGRAM A ;
                VARS 
                a, b, c : INT;
                d,e,f: FLOAT;
                VOID main(aa : INT, bb: FLOAT) {                    
                    VARS
                    ab : FLOAT;
                    {                        
                        ab = aa + bb;
                        PRINT("a");
                    }
                    
                }; 
                                
                BEGIN { 
                    WHILE(a > b) DO 
                        IF(a > c){
                            PRINT("a es mayor que c");
                        } ELSE {
                            PRINT("a no es mayor que c");
                        };
                    };
                } END
            ''',
            "description": "Un programa que contiene una estructura WHILE sin llaves que envuelvan su bloque de código, lo que debería causar un error de análisis sintáctico debido a la falta de delimitadores adecuados para el bloque del WHILE.",
            "should_parse": False
        },{
            "name" : "TC 9. Programa con if roto",
            "input": '''
                PROGRAM A ;
                VARS 
                a, b, c : INT;
                d,e,f: FLOAT;
                VOID main(aa : INT, bb: FLOAT) {                    
                    VARS
                    ab : FLOAT;
                    {                        
                        ab = aa + bb;
                        PRINT("a");
                    }
                    
                }; 
                                
                BEGIN { 
                    WHILE(a > b) DO {
                        IF(a > c){
                            PRINT("a es mayor que c");
                        } ELSE 
                            PRINT("a no es mayor que c");
                        };
                    };
                } END
            ''',
            "description": "Un programa que contiene una estructura IF sin llaves que envuelvan su bloque ELSE, lo que debería causar un error de análisis sintáctico debido a la falta de delimitadores adecuados para el bloque del ELSE.",
            "should_parse": False
        },{
            "name" : "TC 10. Estatutos vacios",
            "input": '''
                PROGRAM A ;
                VARS 
                a, b, c : INT;
                d,e,f: FLOAT;
                VOID main(aa : INT, bb: FLOAT) {                    
                    VARS
                    ab : FLOAT;
                    {                        
                        ab = aa + bb;
                        PRINT("a");
                    }
                    
                }; 
                                
                BEGIN { 
                    WHILE(a > b) DO {
                        IF(a > c){
                        } ELSE {
                        };
                    };
                } END
            ''',
            "description": "Un programa que incluye estructuras de control IF y WHILE con bloques vacíos, lo que debería ser válido sintácticamente aunque no realice ninguna operación dentro de esos bloques.",
            "should_parse": True
        },{
            "name" : "TC11. LLamada",
            "input": '''
                PROGRAM A ;
                VARS 
                a, b, c : INT;
                d,e,f: FLOAT;
                VOID main(aa : INT, bb: FLOAT) {                    
                    VARS
                    ab : FLOAT;
                    {                        
                        ab = aa + bb;
                        PRINT("a");
                    }
                    
                    
                }; 
                                
                BEGIN { 
                    WHILE(a > b) DO {
                        IF(a > c){
                            PRINT("a es mayor que c");
                        } ELSE {
                            funcion_test(1,2);
                        };
                    };
                } END
            ''',
            "description": "Un programa que incluye una llamada a función dentro de un bloque ELSE, lo que debería ser válido",
            "should_parse": True
        }
    ]

def run_tests():
    test_cases_list = test_cases()
    for index, test_case in enumerate(test_cases_list, start=1):
        print(f"\nDescripción de TC{index}: {test_case['description']} \n progress: {index}/{len(test_cases_list)}")
        print(f" Running {test_case['name']}...  ")
        try:
            patito.parse(test_case["input"])
            if test_case["should_parse"]:
                print("  PASSED")
            else:
                print("  FAILED: Expected to fail but parsed successfully.")
        except Exception as e:
            if test_case["should_parse"]:
                print(f"  FAILED: Expected to parse but got error: {e}")
            else:
                print("  PASSED")

                
if __name__ == "__main__":
    run_tests() 
    

