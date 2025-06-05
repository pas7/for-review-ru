from enum import Enum
import re
from typing import Optional, Dict

from deep_translator import GoogleTranslator
from IPython.display import display, HTML, clear_output
import mysql.connector


class Language(Enum):
    DE = 'de'
    RU = 'ru'
    NONE = None


def custom() -> None:
    """delete padding in Jupyter notebook"""
    custom_css = """
    <style>
      .container {
          width: 100% !important;
          padding-left: 0 !important;
          padding-right: 0 !important;
      }
    </style>
    """
    display(HTML(custom_css))


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """translate `text` from `source_lang` to `target_lang`"""
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translation = translator.translate(text)
    except Exception as e:
        print(f"An error occurred during translation: {e}")
        translation = ""
    return translation


def get_query_by_keyword(keyword: str) -> str:
    """get query by keyword"""
    keyword = keyword.lower()
    query = f"""
    select distinct plot, genres, `cast`, title, directors, `year`, `imdb.rating`
    from movies 
    where lower(plot) like '%{keyword}%'
       or lower(genres) like '%{keyword}%'
       or lower(`cast`) like '%{keyword}%'
       or lower(title) like '%{keyword}%'
       or lower(`year`) like '%{keyword}%'
       or lower(directors) like '%{keyword}%'
    order by `imdb.rating` desc
    limit 10;
    """
    return query


def get_query_by_genre_year(genre: str, year: str) -> str:
    """get query by genre and year"""
    genre = genre.lower()
    query = f"""
    select distinct plot, genres, `cast`, title, directors, `year`, `imdb.rating`
    from movies 
    where lower(genres) like "%{genre}%" and year={year}
    order by `imdb.rating` desc
    limit 10;
    """
    return query


def get_query_for_top_keywords() -> str:
    """get query for TOP-10 keywords"""
    query = """
    select lower(word) as word, count(*) as freq
    from history_words
    group by lower(word)
    order by freq desc
    limit 10;
    """
    return query


html = """
<style>
  table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed; /* Устанавливаем фиксированную ширину таблицы */
  }
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left !important; /* Выравниваем текст в ячейках влево */
    word-wrap: break-word; /* Разрешаем перенос слов */
  }
  th {
    padding-top: 12px;
    padding-bottom: 12px;
    background-color: #f2f2f2;
  }
  .narrow {
    width: 50px; /* Устанавливаем начальную ширину */
    white-space: normal; /* Позволяем перенос текста */
    word-break: break-word; /* Перенос слов при необходимости */
  }
  .narrow_mid {
    width: 180px; /* Устанавливаем начальную ширину */
    white-space: normal; /* Позволяем перенос текста */
    word-break: break-word; /* Перенос слов при необходимости */
  }
</style>
<style>
span.hoverable {
  position: relative;
  cursor: pointer;
}
span.hoverable::after {
  content: attr(data-fulltext);
  position: absolute;
  white-space: normal;
  background: #333;
  color: #fff;
  padding: 5px;
  border-radius: 5px;
  top: 1.5em;
  left: 0;
  text-align: left;
  z-index: 1000;
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
  width: 500px; /* Установим фиксированную ширину всплывающего блока */
  word-wrap: break-word;
}
span.hoverable:hover::after {
  opacity: 1;
}
</style>
<table>
  <tr>
    <th class="narrow">#</th> <!-- Добавляем узкую колонку для номера по порядку -->
    <th class="narrow">Rating</th>
    <th class="narrow">Year</th>
    <th class="narrow_mid">Title</th>
    <th class="narrow_mid">Genres</th>
    <th>Cast</th>
    <th class="narrow_mid">Directors</th>
  </tr>
"""


def highlight(text: str, keyword: str) -> str:
    """highlight `keyword` in `text` for print html"""
    text = str(text)
    if keyword == '': return text
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    highlighted_text = pattern.sub(
        lambda match: f'<span style="color: red;">{match.group(0)}</span>',
        text
    )
    return highlighted_text


class MySql():
    def __init__(self, config: Dict[str, str], translate: Optional[str] = None) -> None:
        self.config = config
        self.html = html
        self.translate = translate
        try:
            connection = mysql.connector.connect(**self.config)
            print('OK')
            connection.close()
        except Exception as e:
            print(f"Failed to connect. Check your config and try again.: {e}")

    def print_movies(self, query: str, keyword: str = '') -> None:
        """print movies to html table"""
        connection = mysql.connector.connect(**self.config)
        cursor = connection.cursor()

        if self.translate is not None:
            print("...wait for the translation")

        cursor.execute(query)
        res = cursor.fetchall()
        html = self.html
        for index, row in enumerate(res):
            plot, genres, cast, title, directors, year, rating = row
            genres = ', '.join(genres)
            if cast:
                cast = ', '.join(eval(cast))
            if directors:
                directors = ','.join(eval(directors))

            html += f"""
            <tr>
                <td class="narrow">{index + 1}</td> <!-- Добавляем номер по порядку -->
                <td class="narrow">{rating}</td>
                <td class="narrow">{highlight(year, keyword)}</td>
                <td class="narrow_mid">{highlight(title, keyword)}</td>
                <td class="narrow_mid">{highlight(genres, keyword)}</td>
                <td>{highlight(cast, keyword)}</td>
                <td class="narrow_mid">{highlight(directors, keyword)}</td>
            </tr>
            """

            plot_translate = plot
            lang = ''
            if self.translate is not None:
                plot_translate = translate_text(plot, 'en', self.translate)
                lang = self.translate
            html += f"""
            <tr>
                <td>
                    <span class="hoverable" data-fulltext="{plot_translate}" style="color: #aaa;">{lang}</span>
                </td>
                <td colspan="6">
                    {highlight(plot, keyword)}
                </td>
            </tr>
            """

        html += "</table>"

        display(HTML(html))

        cursor.close()
        connection.close()

    def print_history(self, query: str) -> None:
        """print TOP keywords"""
        connection = mysql.connector.connect(**self.config)
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            res = cursor.fetchall()
            if res:
                print()
                print('TOP-10 keywords:')
                for word, count in res:
                    print(word, '-', count)
            else:
                print('Result is blank!')

        except Exception as e:
            print(f"An error occurred during execute(query): {e}")

        cursor.close()
        connection.close()

    def write_keyword(self, keyword: str) -> None:
        """write keyword from query to `history_words` table"""
        connection = mysql.connector.connect(**self.config)
        cursor = connection.cursor()

        try:
            cursor.execute("insert into history_words (word) values (%s)", (keyword,))
            connection.commit()
        except Exception as e:
            print(f"An error occurred during write keyword: {e}")

        cursor.close()
        connection.close()


def main_dialog(my_sql: MySql) -> None:
    """dialog for user query and answers"""
    while True:
        clear_output(wait=True)
        choice = input("Enter 1, 2, 3 (or 9 for exit): ")

        if choice == "9":
            print("Exit the program.")
            break

        if choice == "1":
            keyword = input("Enter a keyword or 0: ")
            if keyword == '': print('Keyword is blank!')
            elif keyword == "0": continue
            else:
                query = get_query_by_keyword(keyword)
                my_sql.print_movies(query, keyword)
                my_sql.write_keyword(keyword)

        elif choice == "2":
            genre = input("Enter movie genre (or 0): ")
            if genre == '':
                print('Genre is blank!')
                continue
            if genre == "0": continue

            year = input("Enter year (or 0): ")
            if year == '':
                print('Year is blank!')
                continue
            if year == "0": continue

            query = get_query_by_genre_year(genre, year)
            my_sql.print_movies(query)

        elif choice == "3":
            query = get_query_for_top_keywords()
            my_sql.print_history(query)

        else:
            print("Invalid input. Please enter 1, 2, 3 or 9 (for exit).")
