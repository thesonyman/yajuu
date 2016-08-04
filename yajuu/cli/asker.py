from abc import ABCMeta, abstractmethod
import getpass


class Asker(metaclass=ABCMeta):

    """Abstract class that defines an helper, which prompts the user for input.

    On linux or osx, we can use curses to get a nicer prompt, however on
    windows we must use the builtin input method. The sub-classes of this
    class allow to get user input without worrying about the envrionnment.

    The setup.py file decides to remove the 'inquirer' and 'reachar' modules on
    windows, so that we can easilly check if the user wants to use curses.

    Example of correct use:
    >>> asker = Asker.factory()
    >>> asker.confirm("Do you want to do this?")
    [?] Do you want to do this? (y/N): n

    False
    >>>

    Note:
        Always use the factory method to create the instances, except for
        testing.
    """

    """class: holds the correct class to instantiate."""
    CLASS = None

    @classmethod
    def factory(cls):
        """Return an instance of one of the asker sub-classes.

        This method automatically selects the best class to use for the
        envrionnment."""

        if cls.CLASS is not None:
            return cls.CLASS()

        try:
            import inquirer
        except ImportError:
            inquirer = None

        if inquirer is not None:
            cls.CLASS = InquirerAsker
        else:
            cls.CLASS = StandardAsker

        return cls.CLASS()

    @abstractmethod
    def text(self, message, hidden=False, default=None):
        """Prompt the user for a text input (question).

        The prompt will look like '[?] {message} [{default}]:'.

        Args:
            message (str): The string displayed to the user.
            hidden (Optional[bool]): Whether the user input is displayed.
                Useful for passwords.
            default (Optional[str]): A default value, that the user can erase.

        Returns:
            The string that the user entered, or None if the user cancelled.

        """
        
        pass

    @abstractmethod
    def confirm(self, message, default=False):
        """Prompt the user for a yes / no question.

        The prompt will look like '[?] {message} (Y/n):'.

        Args:
            message (str): The string displayed to the user.
            default (Optional[bool]): A default value, False if not specified.

        Returns:
            The boolean that the user entered, or None if the user cancelled.

        """
        pass

    @abstractmethod
    def select_one(self, message, data):
        """Prompt the user to select an option from a list.

        The prompt will look like '[?] {message}:'.

        Args:
            message (str): The string displayed to the user.
            data (list): A list of tuples, each containing first the printed
                value and the the returned value. The return value can be
                anything.

        Returns:
            The returned value of the selected item, or None if the user
            cancelled.

        """

        pass

    @abstractmethod
    def select_multiple(self, message, data):
        """Prompt the user to select multiple options from a list.

        The prompt will look like '[?] {message}:'.

        Args:
            message (str): The string displayed to the user.
            data (list): A list of tuples, each containing first the printed
                value and the the returned value. The return value can be
                anything.

        Returns:
            list: The return values of the selected items, or None if the
            user cancelled.

        """

        pass


class InquirerAsker(Asker):

    """Uses the inquirer module to prompt the user.

    Note:
        Don't instantiate this class manually, use the Asker factory method.
    """

    def __init__(self):
        self.inquirer = __import__('inquirer')

    def _get_answer(self, question):
        answers = self.inquirer.prompt([question])

        if not answers:
            return None

        return answers[list(answers.keys())[0]]

    def text(self, message, hidden=False, default=None):
        if not hidden:
            if default is None:
                question = self.inquirer.Text('field', message=message)
            else:
                question = self.inquirer.Text(
                    'field', message=message, default=default
                )
        else:
            question = self.inquirer.Password('field', message=message)

        return self._get_answer(question)

    def confirm(self, message, default=False):
        question = self.inquirer.Confirm(
            'field', message=message, default=default
        )
        return self._get_answer(question)

    def select_one(self, message, data):
        question = self.inquirer.List(
            'field', message=message, choices=[x[0] for x in data]
        )

        answer = self._get_answer(question)

        if answer is None:
            return None

        for shown, result in data:
            if shown == answer:
                return result

        return None

    def select_multiple(self, message, data):
        question = self.inquirer.Checkbox(
            'field', message=message, choices=[x[0] for x in data]
        )

        answer = self._get_answer(question)

        if answer is None:
            return None

        results = []

        for shown, result in data:
            if shown in answer:
                results.append(result)

        return results


class StandardAsker(Asker):

    """Uses the builtin python methods to prompt the user.

    Note:
        Don't instantiate this class manually, use the Asker factory method.
    """

    def text(self, message, hidden=False, default=None):
        if default is None:
            label = '[?] {}: '.format(message)
        else:
            label = '[?] {} [{}]: '.format(message, default)

        user_input = None

        try:
            if hidden:
                user_input = getpass.getpass(label)
            else:
                user_input = input(label)

        except (KeyboardInterrupt, EOFError):
            pass

        # Dirty hack to use KeyboardInterrupt even on windows, which swallows
        # sys.stdin events. We still need to except on ctrl+c and ctrl+d.
        finally:
            if user_input is None:
                print()
            elif user_input == '':
                return default

            return user_input

    def confirm(self, message, default=False):
        confirmed = None

        while confirmed is None:
            user_input = None

            try:
                user_input = input('[?] {} ({}): '.format(
                    message, 'Y/n' if default else 'y/N'
                )).lower().strip()
            except (KeyboardInterrupt, EOFError):
                pass
            finally:
                if user_input is None:
                    print()
                    return None

            if user_input == '':
                confirmed = default
            elif user_input == 'y':
                confirmed = True
            elif user_input == 'n':
                confirmed = False

        return confirmed

    def select_one(self, message, data):
        print('[?] {}:'.format(message))

        for index, item in enumerate(data):
            print('{} - {}'.format(index, item[0]))

        item = None

        while item is None:
            user_input = None

            try:
                user_input = input('>> ')
            except (KeyboardInterrupt, EOFError):
                pass
            finally:
                if user_input is None:
                    print('')
                    return None

            try:
                user_input = int(user_input)

                if user_input < 0:
                    print('No negative integer are accepted.')
                    continue

                item = data[user_input][1]
            except ValueError:
                print('The provided value was not an integer.')
                continue
            except IndexError:
                print('The provided index was not in range.')
                continue

        return item

    def select_multiple(self, message, data):
        print('[?] {}:'.format(message))

        for index, item in enumerate(data):
            print('{} - {}'.format(index, item[0]))

        items = []

        while len(items) <= 0:
            user_input = None

            try:
                user_input = input('>> ')
            except (KeyboardInterrupt, EOFError):
                pass
            finally:
                if user_input is None:
                    print('')
                    return None

            parts = [x.strip() for x in user_input.split(',')]
            has_errors = False

            for part in parts:
                try:
                    index = int(part)

                    if index < 0:
                        print('No negative integer are accepted.')
                        has_errors = True

                    item = data[index]

                    if item[1] not in items:
                        items.append(item[1])
                except ValueError:
                    print('One of the provided value was not an integer.')
                    has_errors = True
                except IndexError:
                    print('One of the provided index was not in range.')
                    has_errors = True

            if has_errors:
                items = []
                continue

        return items
