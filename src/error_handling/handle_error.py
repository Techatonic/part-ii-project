from colorama import Fore


def handle_error(message="An error occurred"):
    print(Fore.RED + message + "\nProgram will now exit")
    exit()
