from abc import ABCMeta, abstractmethod
import getpass

try:
    import inquirer
except ImportError:
    inquirer = None


class Asker(metaclass=ABCMeta):

    @staticmethod
    def factory():
        if inquirer is not None:
            return InquirerAsker()
        else:
            return StandardAsker()

    @abstractmethod
    def text(self, message, hidden=False):
        pass

    @abstractmethod
    def confirm(self, message, default=False):
        pass

    @abstractmethod
    def select_one(self, message, data):
        pass

    @abstractmethod
    def select_multiple(self, message, data):
        pass


class InquirerAsker(Asker):

    def _get_answer(self, question):
        answers = inquirer.prompt([question])

        if not answers:
            return None

        return answers[list(answers.keys())[0]]

    def text(self, message, hidden=False):
        cls = inquirer.Password if hidden else inquirer.Text
        question = cls('field', message=message)
        return self._get_answer(question)

    def confirm(self, message, default=False):
        question = inquirer.Confirm('field', message=message, default=default)
        return self._get_answer(question)

    def select_one(self, message, data):
        question = inquirer.List(
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
        question = inquirer.Checkbox(
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

    def text(self, message, hidden=False):
        label = '[?] {}: '.format(message)
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
