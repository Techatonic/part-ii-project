from src.error_handling.handle_error import handle_error


class CSPProblem:
    def __init__(self):
        self.variables = {}
        self.constraints = []

    def add_variable(self, new_var, domain):
        if new_var in self.variables:
            handle_error("Variable already exists")
        if type(domain) != list:
            handle_error("Domain is not a list")
        self.variables[new_var] = domain
