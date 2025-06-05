from lexer import Token 

class ParserError(Exception):
    def __init__(self, message, token=None):
        if token:
            super().__init__(f"{message} (Token: '{token.value}' [{token.type}] satır: {token.line}, sütun: {token.column})")
        else:
            super().__init__(message)
        self.token = token 

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = None
        self.advance() # current_token'ı başlat

    def advance(self):
        while self.current_token_index < len(self.tokens):
            token = self.tokens[self.current_token_index]
            # Lexer boşluk ve yorumları zaten işaretlediği için Parser'ın bunları atlaması önemli.
            if token.type in ['WHITESPACE', 'COMMENT']:
                self.current_token_index += 1
            else:
                self.current_token = token
                self.current_token_index += 1
                return # Anlamlı bir token bulundu, dur ve dön
        self.current_token = None 

    def eat(self, token_type, token_value=None):
        if self.current_token and self.current_token.type == token_type:
            if token_value is None or self.current_token.value == token_value:
                token = self.current_token
                self.advance()
                return token
        
        # Hata mesajını daha açıklayıcı hale getir
        expected = f"tip: {token_type}"
        if token_value:
            expected += f", değer: '{token_value}'"
        
        found = "hiçbir şey (dosya sonu)"
        if self.current_token:
            found = f"tip: {self.current_token.type}, değer: '{self.current_token.value}'"
        
        raise ParserError(f"Beklenen {expected} fakat {found} bulundu.", self.current_token)

    def parse(self):
        # Ayrıştırmanın baştan başlamasını sağlamak için dizini sıfırla ve ilerle
        self.current_token_index = 0
        self.advance() 
        return self.program()

    def program(self):
        statements = []
        # current_token None olana kadar (dosya sonu) veya bir '{' bloğu bitene kadar devam et
        while self.current_token and not (self.current_token.type == 'OPERATOR' and self.current_token.value == '}'):
            stmt = self.statement()
            statements.append(stmt)
            
        return {'type': 'Program', 'statements': statements}

    def statement(self):
        if self.current_token is None:
            raise ParserError("Beklenmedik dosya sonu, bir ifade bekleniyor.", self.current_token)

        if self.current_token.type == 'KEYWORD':
            if self.current_token.value == 'if':
                return self.if_statement()
            elif self.current_token.value == 'while':
                return self.while_statement()
            elif self.current_token.value == 'for':
                return self.for_statement()
            elif self.current_token.value == 'def':
                return self.function_definition()
            elif self.current_token.value == 'return':
                return self.return_statement()
        elif self.current_token.type == 'IDENTIFIER':
            temp_index = self.current_token_index 
            next_meaningful_token = None
            while temp_index < len(self.tokens):
                token = self.tokens[temp_index]
                if token.type not in ['WHITESPACE', 'COMMENT']:
                    next_meaningful_token = token
                    break
                temp_index += 1

            if next_meaningful_token:
                if next_meaningful_token.value == '=':
                    return self.assignment()
                elif next_meaningful_token.type == 'OPERATOR' and next_meaningful_token.value in ['+=', '-=', '*=', '/=']:
                    return self.augmented_assignment()
                elif next_meaningful_token.value == '(':
                    return self.function_call()
            return self.expression()

        raise ParserError(f"Beklenmedik ifade başlangıcı: '{self.current_token.value}' (Tip: {self.current_token.type})", self.current_token)

    def if_statement(self):
        self.eat('KEYWORD', 'if')
        self.eat('OPERATOR', '(')
        condition = self.expression()
        self.eat('OPERATOR', ')')
        self.eat('OPERATOR', '{')
        body = self.program() 
        self.eat('OPERATOR', '}')

        else_body = None
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value == 'else':
            self.eat('KEYWORD', 'else')
            self.eat('OPERATOR', '{')
            else_body = self.program() 
            self.eat('OPERATOR', '}')
        
        return {'type': 'IfStatement', 'condition': condition, 'body': body, 'else_body': else_body}

    def while_statement(self):
        self.eat('KEYWORD', 'while')
        self.eat('OPERATOR', '(')
        condition = self.expression()
        self.eat('OPERATOR', ')')
        self.eat('OPERATOR', '{')
        body = self.program()
        self.eat('OPERATOR', '}')
        return {'type': 'WhileStatement', 'condition': condition, 'body': body}
    
    def for_statement(self):
        self.eat('KEYWORD', 'for')
        self.eat('OPERATOR', '(')
        iterator = self.eat('IDENTIFIER').value
        self.eat('KEYWORD', 'in')
        range_expr = self.range_expression()
        self.eat('OPERATOR', ')')
        self.eat('OPERATOR', '{')
        body = self.program()
        self.eat('OPERATOR', '}')
        return {'type': 'ForStatement', 'iterator': iterator, 'range': range_expr, 'body': body}

    def function_definition(self):
        self.eat('KEYWORD', 'def')
        name = self.eat('IDENTIFIER').value
        self.eat('OPERATOR', '(')
        parameters = []
        if self.current_token and self.current_token.type == 'IDENTIFIER':
            parameters = self.parameter_list()
        self.eat('OPERATOR', ')')
        self.eat('OPERATOR', '{')
        body = self.program()
        self.eat('OPERATOR', '}')
        return {'type': 'FunctionDefinition', 'name': name, 'parameters': parameters, 'body': body}

    def parameter_list(self):
        params = [self.eat('IDENTIFIER').value]
        while self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value == ',':
            self.eat('OPERATOR', ',')
            params.append(self.eat('IDENTIFIER').value)
        return params

    def function_call(self):
        name = self.eat('IDENTIFIER').value
        self.eat('OPERATOR', '(')
        arguments = []
        if self.current_token and self.current_token.value != ')':
            arguments = self.argument_list()
        self.eat('OPERATOR', ')')
        return {'type': 'FunctionCall', 'name': name, 'arguments': arguments}
    
    def argument_list(self):
        args = [self.expression()]
        while self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value == ',':
            self.eat('OPERATOR', ',')
            args.append(self.expression())
        return args

    def return_statement(self):
        self.eat('KEYWORD', 'return')
        expr = None
        if self.current_token and (self.current_token.type in ['NUMBER', 'FLOAT', 'STRING', 'IDENTIFIER'] or \
           (self.current_token.type == 'OPERATOR' and self.current_token.value == '(')):
            expr = self.expression()
        return {'type': 'ReturnStatement', 'expression': expr}

    def assignment(self):
        name = self.eat('IDENTIFIER').value
        self.eat('OPERATOR', '=')
        value = self.expression()
        return {'type': 'Assignment', 'name': name, 'value': value}

    def augmented_assignment(self):
        name = self.eat('IDENTIFIER').value
        op_token = self.eat('OPERATOR', None)
        op = op_token.value
        value = self.expression()
        return {'type': 'AugmentedAssignment', 'name': name, 'op': op, 'value': value}
    

    def _parse_binary_operation(self, parse_next_precedence, operators):
        """
        İkili işlemleri soldan sağa öncelikle ayrıştırmak için yardımcı yöntem.
        `parse_next_precedence` bir sonraki yüksek öncelik seviyesi için yöntemdir.
        `operators` mevcut öncelik seviyesi için operatör değerlerinin bir listesidir.
        """
        node = parse_next_precedence()
        while self.current_token and \
              self.current_token.type == 'OPERATOR' and \
              self.current_token.value in operators:
            op = self.eat('OPERATOR').value
            right = parse_next_precedence()
            node = {'type': 'BinaryOp', 'left': node, 'op': op, 'right': right}
        return node

    def expression(self):
        # Toplama/çıkarma işlemlerini ele alır (en düşük öncelik)
        return self._parse_binary_operation(self.comparison, ['+', '-'])

    def comparison(self):
        # Karşılaştırma operatörlerini ele alır
        return self._parse_binary_operation(self.term, ['==', '!=', '<', '>', '<=', '>='])
    
    def term(self):
        # Çarpma/bölme işlemlerini ele alır
        return self._parse_binary_operation(self.factor, ['*', '/'])

    def factor(self):
        token = self.current_token

        if token is None:
            raise ParserError("Beklenmedik dosya sonu, bir ifade bekleniyor.", token)

        if token.type == 'NUMBER':
            self.eat('NUMBER')
            return {'type': 'Number', 'value': int(token.value)}
        elif token.type == 'FLOAT':
            self.eat('FLOAT')
            return {'type': 'Float', 'value': float(token.value)}
        elif token.type == 'STRING':
            self.eat('STRING')
            return {'type': 'String', 'value': token.value.strip('"')}
        elif token.type == 'IDENTIFIER':
            temp_index = self.current_token_index
            next_meaningful_token = None
            while temp_index < len(self.tokens):
                token_peek = self.tokens[temp_index]
                if token_peek.type not in ['WHITESPACE', 'COMMENT']:
                    next_meaningful_token = token_peek
                    break
                temp_index += 1

            if next_meaningful_token and next_meaningful_token.value == '(':
                return self.function_call()
            else:
                self.eat('IDENTIFIER')
                return {'type': 'Identifier', 'value': token.value}
        elif token.type == 'OPERATOR' and token.value == '(':
            self.eat('OPERATOR', '(')
            node = self.expression() # Parantez içindeki ifadeyi ayrıştır
            self.eat('OPERATOR', ')')
            return {'type': 'ParenthesizedExpression', 'expression': node} # AST'de parantezleri temsil et
        
        raise ParserError(f"Beklenmedik faktör: '{token.value}' (Tip: {token.type})", token)

    def range_expression(self):
        self.eat('KEYWORD', 'range')
        self.eat('OPERATOR', '(')
        arg = self.expression()
        self.eat('OPERATOR', ')')
        return {'type': 'RangeExpression', 'argument': arg}
        
        # Tüm token'ları ayrıştırıcıya ilet; parser kendi içinde boşluk/yorumları atlayacak
        parser = Parser(tokens)
        try:
            ast = parser.parse()
            print("Sözdizimi geçerli! AST:")
            print(json.dumps(ast, indent=2))
        except ParserError as e:
            print(f"Sözdizimi Hatası: {e}")
        except Exception as e:
            print(f"Ayrıştırma sırasında beklenmedik bir hata oluştu: {e}")