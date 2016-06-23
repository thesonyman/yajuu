import difflib


def confirm(message, default=True):
    choice = None

    while choice is None:
        try:
            user_input = input(':: {} [{}] '.format(
                message,
                'Y/n' if default else 'y/N'
            )).lower()
        except KeyboardInterrupt:
            choice = False
            continue

        if user_input == '':
            choice = default
        elif user_input == 'y':
            choice = True
        elif user_input == 'n':
            choice = False

    return choice


def select(message, data):
    choice = None

    if len(data) <= 0:
        return False

    for index, row in enumerate(data):
        print('[{}] {}'.format(index, row[0]))

    while choice is None:
        try:
            user_input = input(':: {} (0-{}) [0]: '.format(
                message, len(data) - 1
            )).lower()
        except KeyboardInterrupt:
            choice = False
            continue

        if user_input == '':
            choice = data[0]
            continue
        elif user_input == '-1':
            choice = False
            continue

        try:
            index = int(user_input)
        except ValueError:
            continue

        if 0 <= index < len(data):
            choice = data[index]

    return choice


def select_best_result(query, results):
    return sorted(
        results,
        key=lambda x: difflib.SequenceMatcher(
            a=query.lower(), b=x.SeriesName.lower()
        ).ratio(),
        reverse=True  # Better first
    )[0]
