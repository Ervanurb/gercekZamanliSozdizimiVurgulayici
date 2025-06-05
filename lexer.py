import re

class Token:
    def __init__(self, type, value, start, end, line=None, column=None):
        self.type = type
        self.value = value
        self.start = start
        self.end = end
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token(type='{self.type}', value='{self.value}', start={self.start}, end={self.end}, line={self.line}, column={self.column})"

# Dilimize ait tüm token tipleri
TOKEN_TYPES = {
    'KEYWORD': r'\b(if|else|while|for|def|return|in|range)\b',
    'OPERATOR': r'(\=\=|\!\=|\<\=|\>\=|\+\=|\-\=|\*\=|\/\=|\+|\-|\*|\/|\=|\>|\<|\(|\)|\{|\}|,)',
    'FLOAT': r'\b\d+\.\d+\b',
    'NUMBER': r'\b\d+\b',
    'STRING': r'"[^"]*"',
    'IDENTIFIER': r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
    'MULTI_LINE_COMMENT': r'/\*[\s\S]*?\*/',
    'COMMENT': r'#.*',
    'WHITESPACE': r'\s+',
    'UNKNOWN': r'.' 
}

class Lexer:
    def __init__(self):
        self.token_patterns = []
        # Token tiplerinin işlenme sırası önemlidir
        ordered_token_types = [
            'KEYWORD', 'OPERATOR', 'FLOAT', 'NUMBER', 'STRING', 
            'IDENTIFIER', 'COMMENT', 'WHITESPACE', 'UNKNOWN'
        ]
        for token_type in ordered_token_types:
            pattern = TOKEN_TYPES[token_type]
            self.token_patterns.append((token_type, re.compile(pattern)))

    def tokenize(self, code):
        tokens = []
        position = 0
        line = 1
        column = 0

        while position < len(code):
            match_found = False
            token_start_line = line
            token_start_column = column 

            for token_type, pattern in self.token_patterns:
                match = pattern.match(code, position)
                if match:
                    value = match.group(0)

                    # Boşluk ve yorumları işleme mantığı
                    if token_type == 'WHITESPACE':
                        new_lines_found = value.count('\n')
                        if new_lines_found > 0:
                            line += new_lines_found
                            last_newline_index = value.rfind('\n')
                            column = len(value) - last_newline_index - 1
                        else:
                            column += len(value)
                        
                        position = match.end()
                        match_found = True
                        break # Anlamlı bir token değil, atla ve devam et
                    elif token_type == 'COMMENT' or token_type== 'MULTI_LINE_COMMENT':
                        new_lines_found = value.count('\n')
                        if new_lines_found > 0:
                            line += new_lines_found
                            last_newline_index = value.rfind('\n')
                            column = len(value) - last_newline_index - 1
                        else:
                            column += len(value)
                    else:
                        # Anlamlı token'ı ekle
                        tokens.append(Token(token_type, value, match.start(), match.end(), 
                                             token_start_line, token_start_column))
                        column += len(value)
                        position = match.end()
                        match_found = True
                        break
            
            if not match_found:
                # Hiçbir desene uymayan karakter, UNKNOWN olarak işaretle
                char = code[position]
                tokens.append(Token('UNKNOWN', char, position, position + 1, line, column))
                position += 1
                column += 1
        return tokens

