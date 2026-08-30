# ============================================================
#  Programas de prueba — Patito
# ============================================================

TEST_1 = """
PROGRAM prog1 ;
VARS
    a, b, c, d : INT ;

VOID test (a : INT){
    {
        PRINT(a);
    }
};
BEGIN {

    b = 3 ;
    c = a + b / 0 ;
    test(1);
    PRINT( c ) ;
} END
"""

TEST_2 = """
PROGRAM prog2 ;
VARS
    x : FLOAT ;
    n : INT ;
BEGIN {
    n = 4 ;
    x = 3.14 ;
    x = x * 2.0 + 1.0 ;
    PRINT( "Resultado: " , x ) ;
} END
"""

TEST_3 = """
PROGRAM prog3 ;
VARS
    a, b : INT ;
BEGIN {
    a = 10 ;
    b = 5 ;
    IF ( a > b ) {
        PRINT( "a es mayor" ) ;
    } ELSE {
        PRINT( "b es mayor o igual" ) ;
    } ;
} END
"""

TEST_4 = """
PROGRAM prog4 ;
VARS
    i, suma : INT ;
BEGIN {
    i = 1 ;
    suma = 0 ;
    WHILE ( i < 6 ) DO {
        suma = suma + i ;
        i = i + 1 ;
    } ;
    PRINT( suma ) ;
} END
"""

TEST_5 = """
PROGRAM prog5 ;
VARS
    a, b, res : INT ;
VOID calcular ( x : INT , y : INT ) {
    VARS
        temp: INT ;
    {
        temp = x + y ;
        PRINT( temp ) ;
    }
} ;
BEGIN {
    a = 3 ;
    b = 4 ;
    calcular( a , b ) ;
} END
"""

TEST_6 = """
PROGRAM fibonacci ;
VARS
    r : INT ;
INT fib ( num : INT ) {
    VARS
        a, b, temp, i : INT ;
    {
        a = 0 ;
        b = 1 ;
        i = 0 ;
        WHILE ( i < num ) DO {
            temp = a + b ;
            a = b ;
            b = temp ;
            i = i + 1 ;
        } ;
    }
    RETURN a ;
} ;
BEGIN {
    PRINT( "fib(0):" ) ;
    r = fib( 0 ) ;
    PRINT( r ) ;
    PRINT( "fib(5):" ) ;
    r = fib( 5 ) ;
    PRINT( r ) ;
    PRINT( "fib(10):" ) ;
    r = fib( 10 ) ;
    PRINT( r ) ;
} END
"""

TEST_7 = """
PROGRAM fibonacci_recursivo ;
VARS
    r : INT ;
INT fib ( n : INT ) {
    VARS
        a, b : INT ;
    {
        IF ( n == 0 ) {
            a = 0 ;
        } ELSE {
            IF ( n == 1 ) {
                a = 1 ;
            } ELSE {
                a = fib( n - 1 ) + fib( n - 2 ) ;
                a = a + b ;
            } ;
        } ;
    }
    RETURN a ;
} ;
BEGIN {
    PRINT( "fib(0):" ) ;
    r = fib( 0 ) ;
    PRINT( r ) ;
    PRINT( "fib(5):" ) ;
    r = fib( 5 ) ;
    PRINT( r ) ;
    PRINT( "fib(10):" ) ;
    r = fib( 10 ) ;
    PRINT( r ) ;
} END
"""

TEST_8 = """
PROGRAM factorial ;
VARS
    r : INT ;
INT fact ( n : INT ) {
    VARS
        res : INT ;
    {
        IF ( n == 0 ) {
            res = 1 ;
        } ELSE {
            res = n * fact( n - 1 ) ;
        } ;
    }
    RETURN res ;
} ;
BEGIN {
    PRINT( "fact(0):" ) ;
    r = fact( 0 ) ;
    PRINT( r ) ;
    PRINT( "fact(5):" ) ;
    r = fact( 6) ;
    PRINT( r ) ;
    PRINT( "fact(10):" ) ;
    r = fact( 10 ) ;
    PRINT( r ) ;
} END
"""


TEST_9 = """
PROGRAM pelos ;
VARS
    i,j : INT ;

INT uno (x : INT){
    {
    }
    RETURN(x*2);

};

INT dos (x : INT){
    {

    }
    RETURN (x*uno(x));
};
BEGIN {

    i = 5;
    PRINT( dos(i+3-1) ) ;
} END
"""