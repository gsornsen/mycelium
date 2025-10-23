# Source: wizard-integration.md
# Line: 725
# Valid syntax: True
# Has imports: False
# Has assignments: False

def custom_screen(self) -> dict:
    """Show custom configuration screen.

    Returns:
        dict: Configuration with keys:
            - option1 (str): Description
            - option2 (bool): Description

    Example:
        >>> screens = CustomScreens(state)
        >>> config = screens.custom_screen()
        >>> print(config["option1"])
    """