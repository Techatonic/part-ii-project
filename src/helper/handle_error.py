from colorama import Fore


def handle_error(message: str = "An error occurred", exit_program: bool = True) -> None:
    print()
    print(Fore.RED + message)
    if exit_program:
        print("Program will now exit")
        exit()
    print(Fore.RESET)  # change back to normal
