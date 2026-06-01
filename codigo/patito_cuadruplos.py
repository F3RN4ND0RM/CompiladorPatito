# ============================================================
#  Compilador Patito — Generador de Cuádruplos
#  Etapa 3: Pilas, Fila y Traducción a Cuádruplos
# ============================================================

import importlib.util, os as _os
from lark import Tree, Token
from patito import patito
import patito_semantica as _sem  

# para acceder a DirectorioFunciones, SemanticError y consultar_cubo
DirectorioFunciones = _sem.DirectorioFunciones
SemanticError       = _sem.SemanticError
consultar_cubo      = _sem.consultar_cubo


# ============================================================
#  Pila genérica (LIFO)
# ============================================================

class Pila:
    """
    Pila genérica de uso en el compilador.
    Se instancia una pila para Operadores, una para Operandos
    y una para Tipos durante la generación de cuádruplos.
    """
    def __init__(self, nombre: str = "Pila"):
        self.nombre = nombre
        self._datos: list = []

    def push(self, valor) -> None:
        self._datos.append(valor)

    def pop(self):
        if self.vacia():
            raise IndexError(f"Pop en pila vacía: {self.nombre}")
        return self._datos.pop()

    def tope(self):
        return self._datos[-1] if self._datos else None

    def vacia(self) -> bool:
        return len(self._datos) == 0

    def __len__(self) -> int:
        return len(self._datos)

    def __repr__(self) -> str:
        return f"Pila({self.nombre}){self._datos}"


# ============================================================
#  Fila de Cuádruplos (FIFO)
# ============================================================
class FilaCuadruplos:
    """
    Fila (cola) de cuádruplos generados por el compilador.
    Cada cuádruplo tiene la forma: (operador, arg1, arg2, resultado).
    Soporta backpatching mediante el método `completar`.
    """
    def __init__(self):
        self._fila: list[tuple] = []

    def agregar(self, op, arg1, arg2, resultado) -> int:
        """Agrega un cuádruplo y retorna su índice."""
        self._fila.append((op, arg1, arg2, resultado))
        return len(self._fila) - 1

    def completar(self, idx: int, campo: int, valor) -> None:
        """Rellena un campo pendiente (_) en un cuádruplo existente (backpatching)."""
        q = list(self._fila[idx])
        q[campo] = valor
        self._fila[idx] = tuple(q)

    def siguiente(self) -> int:
        """Retorna el índice del próximo cuádruplo a generar."""
        return len(self._fila)

    def __len__(self) -> int:
        return len(self._fila)

    def __iter__(self):
        return iter(self._fila)

    def __repr__(self) -> str:
        encabezado = f"{'#':<5} {'Op':<10} {'Arg1':<15} {'Arg2':<15} {'Resultado'}"
        sep = "-" * 58
        filas = [
            f"{i:<5} {str(op):<10} {str(a1):<15} {str(a2):<15} {str(res)}"
            for i, (op, a1, a2, res) in enumerate(self._fila)
        ]
        return "\n".join([encabezado, sep] + filas) if filas else f"{encabezado}\n{sep}\n(vacía)"


# ============================================================
#  Generador de Cuádruplos
# ============================================================

class GeneradorCuadruplos:
    """
    Recorre el árbol sintáctico producido por Lark y genera
    cuádruplos usando tres pilas (operadores, operandos, tipos)
    y una fila de cuádruplos.
    """

    def __init__(self):
        self.dir_funcs  = DirectorioFunciones()
        self.pila_ops   = Pila("Operadores")
        self.pila_ands  = Pila("Operandos")
        self.pila_tipos = Pila("Tipos")
        self.fila       = FilaCuadruplos()

    # ── Utilidades ──────────────────────────────────────────

    def _nuevo_temp(self, tipo: str) -> int:
        return self.dir_funcs.asignar_nueva_temporal(tipo)

    def _generar_cuad(self) -> None:
        """
        Punto neurálgico P_GEN:
        Extrae el operador del tope de pila_ops, extrae dos operandos/tipos
        de pila_ands/pila_tipos, consulta el cubo semántico,
        genera el cuádruplo y empuja el temporal resultado.
        """
        op       = self.pila_ops.pop()
        der      = self.pila_ands.pop();  tipo_der  = self.pila_tipos.pop()
        izq      = self.pila_ands.pop();  tipo_izq  = self.pila_tipos.pop()
        tipo_res = consultar_cubo(tipo_izq, tipo_der, op)
        if tipo_res == "x":
            raise SemanticError(f"Operación inválida: {tipo_izq} {op} {tipo_der}")
        temp = self._nuevo_temp(tipo_res)
        self.fila.agregar(op, izq, der, temp)
        self.pila_ands.push(temp)
        self.pila_tipos.push(tipo_res)

    # ── programa ────────────────────────────────────────────

    def compilar(self, codigo: str) -> FilaCuadruplos:
        arbol = patito.parse(codigo)
        self._programa(arbol)
        return self.fila

    def _programa(self, t: Tree):
        nombre = str(t.children[1])
        self.dir_funcs.insertar_funcion(nombre, "VOID")
        for child in t.children:
            if isinstance(child, Tree):
                if   child.data == "programa_":  self._programa_(child)
                elif child.data == "programa__": self._programa__(child)
                elif child.data == "cuerpo":     self._cuerpo(child)

    def _programa_(self, t: Tree):
        for child in t.children:
            if isinstance(child, Tree) and child.data == "vars":
                self._vars(child)

    def _programa__(self, t: Tree):
        for child in t.children:
            if isinstance(child, Tree):
                if   child.data == "funcs":      self._funcs(child)
                elif child.data == "programa__": self._programa__(child)

    # ── vars ────────────────────────────────────────────────

    def _vars(self, t: Tree):
        for child in t.children:
            if isinstance(child, Tree) and child.data == "vars_":
                self._vars_(child)

    def _vars_(self, t: Tree):
        ids  = []
        tipo = None
        for child in t.children:
            if isinstance(child, Token) and child.type == "TOKEN_ID":
                ids.append(str(child))
            elif isinstance(child, Tree):
                if   child.data == "vars__":  ids += self._vars__(child)
                elif child.data == "tipo":    tipo = self._tipo(child)
                elif child.data == "vars___": self._vars___(child)
        for id_ in ids:
            self.dir_funcs.insertar_variable(id_, "VAR", tipo)

    def _vars__(self, t: Tree) -> list:
        ids = []
        for child in t.children:
            if isinstance(child, Token) and child.type == "TOKEN_ID":
                ids.append(str(child))
            elif isinstance(child, Tree) and child.data == "vars__":
                ids += self._vars__(child)
        return ids

    def _vars___(self, t: Tree):
        for child in t.children:
            if isinstance(child, Tree) and child.data == "vars_":
                self._vars_(child)

    def _tipo(self, t: Tree) -> str:
        return str(t.children[0])

    # ── funcs ────────────────────────────────────────────────

    def _funcs(self, t: Tree):
        ch = t.children
        if isinstance(ch[0], Token) and ch[0].type == "TOKEN_VOID":
            tipo_ret = "VOID"
            nombre   = str(ch[1])
        else:
            tipo_ret = self._tipo(ch[0])
            nombre   = str(ch[1])

        self.dir_funcs.insertar_funcion(nombre, tipo_ret)
        self.dir_funcs.abrir_scope(nombre)

        for child in t.children:
            if isinstance(child, Tree):
                if   child.data == "funcs_":   self._funcs_params(child)
                elif child.data == "funcs___":  self._funcs___(child)
                elif child.data == "cuerpo":    self._cuerpo(child)
                elif child.data == "funcs____": self._funcs____(child)

        self.dir_funcs.verificar_returnes(nombre)
        self.dir_funcs.cerrar_scope()

    def _funcs_params(self, t: Tree):
        ids   = []
        tipos = []
        for child in t.children:
            if isinstance(child, Token) and child.type == "TOKEN_ID":
                ids.append(str(child))
            elif isinstance(child, Tree):
                if   child.data == "tipo":    tipos.append(self._tipo(child))
                elif child.data == "funcs__":
                    mi, mt = self._funcs__(child)
                    ids += mi; tipos += mt
        for id_, tipo in zip(ids, tipos):
            self.dir_funcs.insertar_variable(id_, "PARAM", tipo)

    def _funcs__(self, t: Tree):
        ids   = []
        tipos = []
        for child in t.children:
            if isinstance(child, Token) and child.type == "TOKEN_ID":
                ids.append(str(child))
            elif isinstance(child, Tree):
                if   child.data == "tipo":    tipos.append(self._tipo(child))
                elif child.data == "funcs__":
                    mi, mt = self._funcs__(child)
                    ids += mi; tipos += mt
        return ids, tipos

    def _funcs___(self, t: Tree):
        for child in t.children:
            if isinstance(child, Tree) and child.data == "vars":
                self._vars(child)

    def _funcs____(self, t: Tree):
        for child in t.children:
            if isinstance(child, Tree) and child.data == "expresion":
                self._expresion(child)
                resultado = self.pila_ands.pop()
                tipo = self.pila_tipos.pop()
                self.dir_funcs.registrar_return(tipo)
                self.fila.agregar("RETURN", resultado, "_", "_")

    # ── cuerpo y estatutos ───────────────────────────────────

    def _cuerpo(self, t: Tree):
        for child in t.children:
            if isinstance(child, Tree) and child.data == "cuerpo_":
                self._cuerpo_(child)

    def _cuerpo_(self, t: Tree):
        for child in t.children:
            if isinstance(child, Tree):
                if   child.data == "estatuto": self._estatuto(child)
                elif child.data == "cuerpo_":  self._cuerpo_(child)

    def _estatuto(self, t: Tree):
        for child in t.children:
            if isinstance(child, Tree):
                if   child.data == "asigna":    self._asigna(child)
                elif child.data == "condicion": self._condicion(child)
                elif child.data == "ciclo":     self._ciclo(child)
                elif child.data == "imprime":   self._imprime(child)
                elif child.data == "llamada":   self._llamada(child)
                elif child.data == "estatuto_": self._estatuto_(child)

    def _estatuto_(self, t: Tree):
        for child in t.children:
            if isinstance(child, Tree):
                if   child.data == "estatuto":  self._estatuto(child)
                elif child.data == "estatuto_": self._estatuto_(child)

    # ── asigna ──────────────────────────────────────────────

    def _asigna(self, t: Tree):
        """
        Punto neurálgico P_ASIGNA:
        Evalúa la expresión derecha, extrae el resultado de pila_ands
        y genera el cuádruplo de asignación (=, fuente, _, destino).
        """
        nombre_var = str(t.children[0])
        registro = self.dir_funcs.obtener_registro_variable(nombre_var)

        for child in t.children:
            if isinstance(child, Tree) and child.data == "expresion":
                self._expresion(child)

        resultado = self.pila_ands.pop()
        self.pila_tipos.pop()
        self.fila.agregar("=", resultado, "_", registro["direccion"])

    # ── imprime ─────────────────────────────────────────────

    def _imprime(self, t: Tree):
        for child in t.children:
            if isinstance(child, Tree) and child.data == "imprime_":
                self._imprime_(child)

    def _imprime_(self, t: Tree):
        ch = t.children
        if ch and isinstance(ch[0], Token) and ch[0].type == "TOKEN_LETRERO":
            direccion = self.dir_funcs.asignar_constante(str(ch[0]), "STRING")
            self.fila.agregar("PRINT", direccion, "_", "_")
            for child in ch[1:]:
                if isinstance(child, Tree) and child.data == "imprime__":
                    self._imprime__(child)
        else:
            for child in t.children:
                if isinstance(child, Tree):
                    if child.data == "expresion":
                        self._expresion(child)
                        res = self.pila_ands.pop()
                        self.pila_tipos.pop()
                        self.fila.agregar("PRINT", res, "_", "_")
                    elif child.data == "imprime__":
                        self._imprime__(child)

    def _imprime__(self, t: Tree):
        for child in t.children:
            if isinstance(child, Tree) and child.data == "imprime_":
                self._imprime_(child)

    # ── condicion (IF / IF-ELSE) ─────────────────────────────

    def _condicion(self, t: Tree):
        """
        Puntos neurálgicos:
          P_IF_COND  → evalúa la expresión condicional
          P_GOTOF    → genera GOTOF con destino pendiente
          P_IF_BODY  → genera el cuerpo del IF
          P_GOTO     → (si hay ELSE) genera GOTO con destino pendiente
          P_FILL_IF  → rellena el destino del GOTOF
          P_ELSE_BODY→ genera el cuerpo del ELSE
          P_FILL_ELSE→ rellena el destino del GOTO
        """
        exp_node  = None
        if_cuerpo = None
        cond__    = None

        for child in t.children:
            if isinstance(child, Tree):
                if   child.data == "expresion":  exp_node  = child
                elif child.data == "cuerpo":     if_cuerpo = child
                elif child.data == "condicion_": cond__    = child

        # P_IF_COND
        self._expresion(exp_node)
        res_cond = self.pila_ands.pop()
        self.pila_tipos.pop()

        # P_GOTOF
        idx_gotof = self.fila.agregar("GOTOF", res_cond, "_", "_")

        # P_IF_BODY
        self._cuerpo(if_cuerpo)

        # Does ELSE exist?
        else_cuerpo = None
        if cond__ is not None:
            for child in cond__.children:
                if isinstance(child, Tree) and child.data == "cuerpo":
                    else_cuerpo = child

        if else_cuerpo:
            # P_GOTO
            idx_goto = self.fila.agregar("GOTO", "_", "_", "_")
            # P_FILL_IF
            self.fila.completar(idx_gotof, 3, self.fila.siguiente())
            # P_ELSE_BODY
            self._cuerpo(else_cuerpo)
            # P_FILL_ELSE
            self.fila.completar(idx_goto, 3, self.fila.siguiente())
        else:
            # P_FILL_IF
            self.fila.completar(idx_gotof, 3, self.fila.siguiente())

    # ── ciclo (WHILE) ────────────────────────────────────────

    def _ciclo(self, t: Tree):
        """
        Puntos neurálgicos:
          P_WHILE_START → guarda posición de inicio
          P_WHILE_COND  → evalúa expresión condicional
          P_GOTOF       → genera GOTOF con destino pendiente
          P_WHILE_BODY  → genera el cuerpo del ciclo
          P_GOTO_BACK   → genera GOTO de regreso al inicio
          P_FILL_WHILE  → rellena el destino del GOTOF
        """
        exp_node  = None
        cuerpo_n  = None

        for child in t.children:
            if isinstance(child, Tree):
                if   child.data == "expresion": exp_node = child
                elif child.data == "cuerpo":    cuerpo_n = child

        # P_WHILE_START
        pos_inicio = self.fila.siguiente()

        # P_WHILE_COND
        self._expresion(exp_node)
        res_cond = self.pila_ands.pop()
        self.pila_tipos.pop()

        # P_GOTOF
        idx_gotof = self.fila.agregar("GOTOF", res_cond, "_", "_")

        # P_WHILE_BODY
        self._cuerpo(cuerpo_n)

        # P_GOTO_BACK
        self.fila.agregar("GOTO", "_", "_", pos_inicio)

        # P_FILL_WHILE
        self.fila.completar(idx_gotof, 3, self.fila.siguiente())

    # ── llamada ─────────────────────────────────────────────

    def _llamada(self, t: Tree) -> tuple:
        nombre_func = str(t.children[0])
        if not self.dir_funcs.existe_funcion(nombre_func):
            raise SemanticError(f"Función no declarada: '{nombre_func}'")

        tipos_args = []
        for child in t.children:
            if isinstance(child, Tree) and child.data == "llamada_":
                self._llamada_(child, tipos_args)

        self.dir_funcs.verificar_llamada(nombre_func, tipos_args)

        func_info = self.dir_funcs.buscar_funcion(nombre_func)
        tipo_ret  = func_info["tipo_retorno"] if func_info else "VOID"

        if tipo_ret == "VOID":
            self.fila.agregar("CALL", nombre_func, "_", "_")
            return None, tipo_ret

        temp = self._nuevo_temp(tipo_ret)
        self.fila.agregar("CALL", nombre_func, "_", temp)
        return temp, tipo_ret

    def _llamada_(self, t: Tree, tipos_args: list):
        for child in t.children:
            if isinstance(child, Tree):
                if child.data == "expresion":
                    self._expresion(child)
                    res  = self.pila_ands.pop()
                    tipo = self.pila_tipos.pop()
                    tipos_args.append(tipo)
                    self.fila.agregar("PARAM", res, "_", "_")
                elif child.data == "llamada__":
                    self._llamada__(child, tipos_args)

    def _llamada__(self, t: Tree, tipos_args: list):
        for child in t.children:
            if isinstance(child, Tree):
                if child.data == "expresion":
                    self._expresion(child)
                    res  = self.pila_ands.pop()
                    tipo = self.pila_tipos.pop()
                    tipos_args.append(tipo)
                    self.fila.agregar("PARAM", res, "_", "_")
                elif child.data == "llamada__":
                    self._llamada__(child, tipos_args)

    # ── expresiones ─────────────────────────────────────────

    def _expresion(self, t: Tree):
        """expresion: exp expresion_"""
        for child in t.children:
            if isinstance(child, Tree):
                if   child.data == "exp":         self._exp(child)
                elif child.data == "expresion_":  self._expresion_(child)

    def _expresion_(self, t: Tree):
        """expresion_: expresion__ | ε"""
        for child in t.children:
            if isinstance(child, Tree) and child.data == "expresion__":
                self._expresion__(child)

    def _expresion__(self, t: Tree):
        """
        Punto neurálgico P_PUSH_OP_REL:
        expresion__: TOKEN_GT exp | TOKEN_LT exp | TOKEN_DIFF exp | TOKEN_ISEQUAL exp
        Empuja el operador relacional y genera el cuádruplo relacional.
        """
        op = None
        for child in t.children:
            if isinstance(child, Token):
                op = str(child)
            elif isinstance(child, Tree) and child.data == "exp":
                self.pila_ops.push(op)
                self._exp(child)
                self._generar_cuad()

    def _exp(self, t: Tree):
        """exp: termino exp_"""
        for child in t.children:
            if isinstance(child, Tree):
                if   child.data == "termino": self._termino(child)
                elif child.data == "exp_":    self._exp_(child)

    def _exp_(self, t: Tree):
        """
        Punto neurálgico P_PUSH_OP_SUM:
        exp_: TOKEN_SUM exp | TOKEN_SUBS exp | ε
        Empuja + o - a pila_ops, evalúa el exp derecho y genera cuádruplo.
        """
        op = None
        for child in t.children:
            if isinstance(child, Token):
                op = str(child)
            elif isinstance(child, Tree) and child.data == "exp":
                self.pila_ops.push(op)
                self._exp(child)
                self._generar_cuad()

    def _termino(self, t: Tree):
        """termino: factor termino_"""
        for child in t.children:
            if isinstance(child, Tree):
                if   child.data == "factor":   self._factor(child)
                elif child.data == "termino_": self._termino_(child)

    def _termino_(self, t: Tree):
        """
        Punto neurálgico P_PUSH_OP_MUL:
        termino_: TOKEN_TIMES termino | TOKEN_DIV termino | ε
        Empuja * o / a pila_ops, evalúa el termino derecho y genera cuádruplo.
        """
        op = None
        for child in t.children:
            if isinstance(child, Token):
                op = str(child)
            elif isinstance(child, Tree) and child.data == "termino":
                self.pila_ops.push(op)
                self._termino(child)
                self._generar_cuad()

    def _factor(self, t: Tree):
        """
        factor: TOKEN_LPAREN expresion TOKEN_RPAREN
              | TOKEN_SUM factor_
              | TOKEN_SUBS factor_
              | factor_
              | llamada
        """
        ch = t.children

        # (expresion)
        if any(isinstance(c, Token) and c.type == "TOKEN_LPAREN" for c in ch):
            for child in ch:
                if isinstance(child, Tree) and child.data == "expresion":
                    self._expresion(child)
            return

        # Unary sign
        sign = None
        for child in ch:
            if isinstance(child, Token) and child.type in ("TOKEN_SUM", "TOKEN_SUBS"):
                sign = str(child)

        for child in ch:
            if isinstance(child, Tree):
                if child.data == "factor_":
                    self._factor_(child)
                    if sign == "-":
                        val  = self.pila_ands.pop()
                        tipo = self.pila_tipos.pop()
                        temp = self._nuevo_temp(tipo)
                        self.fila.agregar("NEG", val, "_", temp)
                        self.pila_ands.push(temp)
                        self.pila_tipos.push(tipo)
                    return
                elif child.data == "llamada":
                    temp, tipo_ret = self._llamada(child)
                    if tipo_ret == "VOID":
                        raise SemanticError(
                            f"Función '{str(child.children[0])}' no puede usarse como expresión"
                        )
                    self.pila_ands.push(temp)
                    self.pila_tipos.push(tipo_ret)
                    return

    def _factor_(self, t: Tree):
        """
        Punto neurálgico P_PUSH_OPERAND:
        factor_: cte | TOKEN_ID
        Empuja el operando y su tipo a pila_ands / pila_tipos.
        """
        ch = t.children
        if isinstance(ch[0], Tree) and ch[0].data == "cte":
            val, tipo = self._cte(ch[0])
            direccion = self.dir_funcs.asignar_constante(val, tipo)
            self.pila_ands.push(direccion)
            self.pila_tipos.push(tipo)
        elif isinstance(ch[0], Token) and ch[0].type == "TOKEN_ID":
            nombre = str(ch[0])
            registro = self.dir_funcs.obtener_registro_variable(nombre)
            self.pila_ands.push(registro["direccion"])
            self.pila_tipos.push(registro["tipo"])

    def _cte(self, t: Tree) -> tuple:
        token = t.children[0]
        if token.type == "TOKEN_CTE_FLOAT":
            return (str(token), "FLOAT")
        return (str(token), "INT")


# ============================================================
#  Programas de prueba
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
    
    a = d ;
    b = 3 ;
    c = a + b * 2 ;
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
        temp : INT ;
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


def compilar_y_mostrar(nombre: str, codigo: str) -> None:
    print("=" * 60)
    print(f"  {nombre}")
    print("=" * 60)
    gen = GeneradorCuadruplos()
    try:
        gen.compilar(codigo)
        print(gen.fila)
    except Exception as e:
        print(f"ERROR: {e}")
    print()


if __name__ == "__main__":
    compilar_y_mostrar("TEST 1 — Expresiones aritméticas",     TEST_1)
    compilar_y_mostrar("TEST 2 — Flotantes y PRINT con letrero", TEST_2)
    compilar_y_mostrar("TEST 3 — Condicional IF-ELSE",           TEST_3)
    compilar_y_mostrar("TEST 4 — Ciclo WHILE",                   TEST_4)
    compilar_y_mostrar("TEST 5 — Función y llamada",             TEST_5)
