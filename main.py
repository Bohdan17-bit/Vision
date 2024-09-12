from openpyxl import load_workbook
from model import Model


def find_freq_for_word(sheet, column, word):
    for cell in column:
        if word == cell.value:
            return sheet.cell(row=cell.row, column=21).value
    return "not found!"


def show_time_to_read(time, sd_time):
    sec = time // 1000
    ms = time % 1000
    print(f"You need {int(sec)} seconds and {round(ms, 3)} ms to read those text.")
    sec_sd = sd_time // 1000
    ms_sd = sd_time % 1000
    print(f"Standard deviation equal {int(sec_sd)} seconds and {round(ms_sd, 3)} ms.")


def get_frequency_dictionary(path):
    return load_workbook(path)


def get_sheet_workbook(workbook, sheet):
    list_sheets = workbook.sheetnames
    if sheet in list_sheets:
        return workbook[sheet]
    else:
        return None


def get_biggest_frequency(sheet):
    return sheet.cell(row=2, column=21).value


def get_column_by_sheet(sheet, name):
    return sheet[name]


if __name__ == "__main__":
    model = Model()
    model.read_text_from_site("https://ua.sinoptik.ua")
    model.set_distance_to_display(40)

    words_spans = model.get_text_list_spans()

    for word in words_spans:
        print(f"{repr(word.text_span)}")

    print("Loading frequency dictionary...")

    workbook = get_frequency_dictionary('data/wordFrequency.xlsx')
    sheet = get_sheet_workbook(workbook, "4 forms (219k)")

    if not sheet:
        print("Sheet not found!")
        exit()

    column_b = get_column_by_sheet(sheet, 'B')
    biggest_value_freq = get_biggest_frequency(sheet)

    rest_letters = 0
    state = "updated"

    for word in words_spans:
        if word.text_span.isalpha():
            print(f"Next word : {word.text_span}")

            if rest_letters > 3:
                rest_letters = 3

            index_chose = 0

            dict_probability = model.calculate_probability_landing(word.text_span, rest_letters)

            print(f"Index calculated for word : <{word.text_span}>")

            if state == "updated":
                index_chose = model.calculate_final_pos_fixation(dict_probability)

            if state == "2 symbols after word":
                index_chose = 0
                state = "updated"

            if word.distance_to_next_span > 0:
                index_chose = len(word.text_span) - 1
                print("End of this word...")

            if word.is_last_in_line:
                index_chose = len(word.text_span) - 1
                print("End of line...")

            if index_chose == len(word.text_span):
                print("Word was skipped! Landing on next symbol!")
                rest_letters = 0

            elif index_chose > len(word.text_span):
                print("Word was skipped! Landing after word on 2 symbols!")
                rest_letters = 0
                state = "2 symbols after word"

            else:
                print(f"Fixation in <{word.text_span}> on symbol {word.text_span[index_chose]}!")
                rest_letters = len(word.text_span) - index_chose
                prob_refix = model.calculate_probability_refixation(word.text_span, index_chose)
                print(f"Chance to refixation = {round(prob_refix, 3)}")

                if model.should_refixate(prob_refix):
                    print("------------------Need to make a refixation------------------")

                    time_refix = model.make_refixation(word.text_span, index_chose + 1)
                    time_refix_sd = model.calculate_sd(time_refix)

                    model.increase_general_time(time_refix)
                    model.increase_general_time_sd(time_refix_sd)

                else:
                    print("We don't need to make a refixation...")

                freq = find_freq_for_word(sheet, column_b, word.text_span)
                time_word_reading = model.calculate_time_reading(word.text_span, index_chose + 1, biggest_value_freq,
                                                                 freq)

                time_to_read_sd = model.calculate_sd(time_word_reading)
                dispersion = model.calculate_normal_distribution(time_word_reading, time_to_read_sd)

                model.increase_general_time(dispersion)

                print("Making a saccade...")

            model.add_average_latency_time()
            model.add_standard_deviation_latency_time()

        else:
            rest_letters += len(word.text_span)

        if word.distance_to_next_span > 0:
            time_saccade = model.calculate_time_saccade(word.distance_to_next_span)
            print(f"Going to next span...It is take {time_saccade} ms\n")
            model.increase_general_time(time_saccade)

    show_time_to_read(model.get_sum_time_reading(), model.get_sum_standard_deviation())
    print("End of reading.")
