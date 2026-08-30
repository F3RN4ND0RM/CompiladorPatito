# ============================================================
#  Compilador Patito — Máquina Virtual
#  Etapa 4: Ejecución de Cuádruplos
# ============================================================
#
#  Mapa de Memoria de Ejecución (direcciones virtuales):
#
#    Segmento   │ Rango        │ Contenido
#    ───────────┼──────────────┼──────────────────────────────
#    global     │ 1000 – 1999  │ Variables globales del programa
#    local      │ 2000 – 2999  │ Variables locales de funciones
#    param      │ 3000 – 3999  │ Parámetros de funciones
#    temp       │ 4000 – 4999  │ Temporales generados por el compilador
#    const      │ 5000 – 5999  │ Constantes literales (solo lectura)
#
#  Estructuras auxiliares:
#    MemoriaEjecucion  → diccionario plano {dirección: valor}
#    RegistroActivacion → frame de llamada (retorno_ip, retorno_dir)
#    MaquinaVirtual    → ejecutor de cuádruplos con IP y pila de llamadas
#
# ============================================================


# ── Mapa de Memoria de Ejecución ────────────────────────────

class MemoriaEjecucion:
    """
    Memoria de ejecución plana.

    Cada variable, parámetro, temporal y constante del programa
    ocupa una dirección virtual única asignada en tiempo de compilación.
    El diccionario interno mapea esa dirección a su valor en tiempo de
    ejecución.

    Los segmentos de direcciones siguen la misma distribución definida
    en MemoriaVirtual:
        global 1000-1999 | local 2000-2999 | param 3000-3999
        temp   4000-4999 | const 5000-5999
    """

    SEGMENTOS = [
        (1000, 1999, "global"),
        (2000, 2999, "local"),
        (3000, 3999, "param"),
        (4000, 4999, "temp"),
        (5000, 5999, "const"),
    ]

    def __init__(self):
        self._mem: dict[int, object] = {}

    def segmento(self, addr: int) -> str:
        for base, tope, nombre in self.SEGMENTOS:
            if base <= addr <= tope:
                return nombre
        raise RuntimeError(f"Dirección virtual fuera de rango: {addr}")

    def leer(self, addr: int) -> object:
        self.segmento(addr)           # valida rango
        return self._mem.get(addr, 0) # 0 como valor por defecto (no inicializado)

    def escribir(self, addr: int, valor: object) -> None:
        if self.segmento(addr) == "const":
            raise RuntimeError(
                f"Escritura ilegal en segmento de constantes: dirección {addr}"
            )
        self._mem[addr] = valor

    def precargar(self, addr: int, valor: object) -> None:
        """Carga un valor de constante en memoria (solo en inicio)."""
        self._mem[addr] = valor

    def dump(self) -> str:
        """Representación de depuración de toda la memoria."""
        lineas = []
        for addr in sorted(self._mem):
            seg = self.segmento(addr)
            lineas.append(f"  [{addr:4d}] ({seg:6}) = {self._mem[addr]!r}")
        return "\n".join(lineas) if lineas else "  (vacía)"


# ── Registro de Activación ───────────────────────────────────

class RegistroActivacion:
    """
    Frame de una llamada a función en la pila de llamadas.

    Almacena:
      - nombre      : nombre de la función llamada
      - retorno_ip  : índice del cuádruplo al que regresar tras ENDPROC/RETURN
      - retorno_dir : dirección donde se guarda el valor de retorno,
                      o None si la función es VOID
    """

    def __init__(self, nombre: str, retorno_ip: int, retorno_dir=None, snapshot=None):
        self.nombre      = nombre
        self.retorno_ip  = retorno_ip
        self.retorno_dir = retorno_dir
        # snapshot de locales/params tomado antes de pisarlos; habilita recursión
        self.snapshot: dict = snapshot if snapshot is not None else {}

    def __repr__(self) -> str:
        return (
            f"RegistroActivacion(func={self.nombre!r}, "
            f"ret_ip={self.retorno_ip}, ret_dir={self.retorno_dir})"
        )


# ── Máquina Virtual ──────────────────────────────────────────

class MaquinaVirtual:
    """
    Máquina virtual de Patito.

    Interpreta la lista de cuádruplos producida por GeneradorCuadruplos
    usando un puntero de instrucción (IP), memoria de ejecución plana y
    una pila de registros de activación.

    Códigos de operación soportados:
        Aritmética  : +  -  *  /  NEG
        Relacional  : >  <  !=  ==
        Asignación  : =
        Salto       : GOTO  GOTOF
        I/O         : PRINT
        Funciones   : PARAM  CALL  RETURN  ENDPROC
        Control     : END
    """

    def __init__(self, gen):
        """
        Parámetros:
            gen : GeneradorCuadruplos ya compilado (gen.compilar() llamado)
        """
        self.cuadruplos: list[tuple]           = list(gen.fila)
        self.dir_funcs                          = gen.dir_funcs
        self.memoria: MemoriaEjecucion          = MemoriaEjecucion()
        self.pila_llamadas: list[RegistroActivacion] = []
        self.pila_params: list                  = []   # staging antes de CALL
        self.ip: int                            = 0

        # Precargar constantes en memoria
        for addr, valor in gen.dir_funcs._memoria.get_constantes_valores().items():
            self.memoria.precargar(addr, valor)

    # ── Helpers ──────────────────────────────────────────────

    def _snapshot_func(self, nombre: str) -> dict:
        """Captura los valores actuales de locales y params de una función"""
        func = self.dir_funcs._directorio.get(nombre, {})
        tabla = func.get("tabla_vars", None)
        if tabla is None:
            return {}
        return {
            reg["direccion"]: self.memoria._mem.get(reg["direccion"], 0)
            for reg in tabla._tabla.values()
        }

    def _nombre_por_dir(self, addr: int) -> str:
        """Devuelve 'nombre (en funcion)' para mensajes de error legibles."""
        for nombre_func, func in self.dir_funcs._directorio.items():
            tabla = func.get("tabla_vars", None)
            if tabla:
                for nombre_var, reg in tabla._tabla.items():
                    if reg["direccion"] == addr:
                        return f"'{nombre_var}' (en {nombre_func})"
        return f"direccion {addr}"

    # ── Acceso a memoria con centinela "_" ───────────────────

    def _leer(self, addr) -> object:
        if addr == "_":
            raise RuntimeError("Intento de leer campo vacio '_'")
        seg = self.memoria.segmento(addr)
        if seg in ("global", "local") and addr not in self.memoria._mem:
            raise RuntimeError(
                f"Variable {self._nombre_por_dir(addr)} "
                f"usada antes de ser inicializada"
            )
        return self.memoria.leer(addr)

    def _escribir(self, addr, valor) -> None:
        if addr == "_":
            return  # campo no utilizado; no hace nada
        self.memoria.escribir(addr, valor)

    # ── Ciclo principal de ejecución ─────────────────────────

    def ejecutar(self) -> None:
        self.ip = 0
        while self.ip < len(self.cuadruplos):
            op, arg1, arg2, res = self.cuadruplos[self.ip]
            self._despachar(op, arg1, arg2, res)

    # ── Despachador de opcodes ───────────────────────────────

    def _despachar(self, op, arg1, arg2, res) -> None:

        # ── Asignación ──────────────────────────────────────
        if op == "=":
            self._escribir(res, self._leer(arg1))
            self.ip += 1

        # ── Aritmética binaria ───────────────────────────────
        elif op == "+":
            self._escribir(res, self._leer(arg1) + self._leer(arg2))
            self.ip += 1

        elif op == "-":
            self._escribir(res, self._leer(arg1) - self._leer(arg2))
            self.ip += 1

        elif op == "*":
            self._escribir(res, self._leer(arg1) * self._leer(arg2))
            self.ip += 1

        elif op == "/":
            divisor = self._leer(arg2)
            if divisor == 0:
                raise RuntimeError(
                    f"División por cero en cuádruplo {self.ip}"
                )
            self._escribir(res, self._leer(arg1) / divisor)
            self.ip += 1

        # ── Negación unaria ──────────────────────────────────
        elif op == "NEG":
            self._escribir(res, -self._leer(arg1))
            self.ip += 1

        # ── Operadores relacionales ──────────────────────────
        elif op == ">":
            self._escribir(res, self._leer(arg1) > self._leer(arg2))
            self.ip += 1

        elif op == "<":
            self._escribir(res, self._leer(arg1) < self._leer(arg2))
            self.ip += 1

        elif op == "!=":
            self._escribir(res, self._leer(arg1) != self._leer(arg2))
            self.ip += 1

        elif op == "==":
            self._escribir(res, self._leer(arg1) == self._leer(arg2))
            self.ip += 1

        elif op == ">=":
            self._escribir(res, self._leer(arg1) >= self._leer(arg2))
            self.ip += 1

        elif op == "<=":
            self._escribir(res, self._leer(arg1) <= self._leer(arg2))
            self.ip += 1

        # ── Salida ───────────────────────────────────────────
        elif op == "PRINT":
            val = self._leer(arg1)
            # Imprimir valor; strings ya fueron limpiados de comillas al precargar
            print(val)
            self.ip += 1

        # ── Saltos ───────────────────────────────────────────
        elif op == "GOTO":
            self.ip = res

        elif op == "GOTOF":
            # Salta si la condición es falsa (False o 0)
            if not self._leer(arg1):
                self.ip = res
            else:
                self.ip += 1

        # ── Paso de parámetros ───────────────────────────────
        elif op == "PARAM":
            # Evalúa el argumento y lo apila para el próximo CALL
            self.pila_params.append(self._leer(arg1))
            self.ip += 1

        # ── Llamada a función ────────────────────────────────
        elif op == "CALL":
            nombre_func = arg1          # string con el nombre de la función
            retorno_dir = None if res == "_" else res

            # Snapshot antes de pisar locales/params (habilita recursión)
            snapshot = self._snapshot_func(nombre_func)
            frame = RegistroActivacion(nombre_func, self.ip + 1, retorno_dir, snapshot)

            # Copiar parámetros en espera a las direcciones del segmento param
            param_dirs = self.dir_funcs.get_params_dir(nombre_func)
            if len(self.pila_params) != len(param_dirs):
                raise RuntimeError(
                    f"CALL '{nombre_func}': se esperaban {len(param_dirs)} "
                    f"param(s), hay {len(self.pila_params)} en la pila"
                )
            for addr, valor in zip(param_dirs, self.pila_params):
                self.memoria._mem[addr] = valor
            self.pila_params.clear()

            self.pila_llamadas.append(frame)
            self.ip = self.dir_funcs.get_inicio_cuad(nombre_func)

        # ── Retorno de función con valor ─────────────────────
        elif op == "RETURN":
            valor = self._leer(arg1)
            frame = self.pila_llamadas.pop()
            # Restaurar snapshot ANTES de escribir el retorno para no pisarlo
            self.memoria._mem.update(frame.snapshot)
            if frame.retorno_dir is not None:
                self._escribir(frame.retorno_dir, valor)
            self.ip = frame.retorno_ip

        # ── Fin de función VOID ──────────────────────────────
        elif op == "ENDPROC":
            frame = self.pila_llamadas.pop()
            self.memoria._mem.update(frame.snapshot)
            self.ip = frame.retorno_ip

        # ── Fin del programa ─────────────────────────────────
        elif op == "END":
            self.ip = len(self.cuadruplos)   # detiene el ciclo principal

        else:
            raise RuntimeError(
                f"Opcode desconocido: '{op}' en cuádruplo {self.ip}"
            )

    # ── Depuración ───────────────────────────────────────────

    def dump_cuadruplos(self) -> str:
        encabezado = f"{'#':<5} {'Op':<10} {'Arg1':<15} {'Arg2':<10} {'Res'}"
        sep = "-" * 55
        filas = [
            f"{i:<5} {str(op):<10} {str(a1):<15} {str(a2):<10} {str(r)}"
            for i, (op, a1, a2, r) in enumerate(self.cuadruplos)
        ]
        return "\n".join([encabezado, sep] + filas)

    def dump_memoria(self) -> str:
        return self.memoria.dump()


# ── Función de conveniencia ──────────────────────────────────

def ejecutar_programa(codigo: str, verbose: bool = False) -> MaquinaVirtual:
    """
    Compila y ejecuta un programa Patito.

    Retorna la MaquinaVirtual para inspección post-ejecución.
    """
    from patito_cuadruplos import GeneradorCuadruplos
    gen = GeneradorCuadruplos()
    gen.compilar(codigo)
    if verbose:
        print(gen.fila)
        print(gen.dir_funcs)
        print()
    mv = MaquinaVirtual(gen)
    mv.ejecutar()
    return mv


# ── Pruebas ──────────────────────────────────────────────────

if __name__ == "__main__":
    from test_programs import TEST_1, TEST_2, TEST_3, TEST_4, TEST_5, TEST_6, TEST_7, TEST_8, TEST_9

    PROGRAMAS = [
         ("TEST 1 — Función void  con parámetro",    TEST_1),
        ("TEST 2 — Flotantes y PRINT con letrero", TEST_2),
        ("TEST 3 — Condicional IF-ELSE",            TEST_3),
        ("TEST 4 — Ciclo WHILE",                    TEST_4),
        ("TEST 5 — Función con dos parámetros",     TEST_5),
        ("TEST 6 — Fibonacci iterativo",            TEST_6),
        ("TEST 7 — Fibonacci recursivo",            TEST_7),
        ("TEST 8 — Factorial recursivo",            TEST_8),
        ("TEST 9 — Función del  pizzaron",    TEST_9)


    ]

    for nombre, codigo in PROGRAMAS:
        sep = "=" * 60
        print(f"\n{sep}\n  {nombre}\n{sep}")
        try:
            mv = ejecutar_programa(codigo, verbose=True)
        except Exception as e:
            import traceback
            print(f"ERROR: {e}")
            traceback.print_exc()
