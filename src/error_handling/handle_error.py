from colorama import Fore


def handle_error(message="An error occurred", exit_program=True):
    print(Fore.RED + message)
    if exit_program:
        print("Program will now exit")
        exit()
