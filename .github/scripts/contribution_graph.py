"""Render GitHub's public contribution calendar without a widget service."""
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'td' and 'data-date' in attrs and 'data-level' in attrs:
            day = date.fromisoformat(attrs['data-date'])
            level = int(attrs['data-level'])
            if level not in range(5):
                raise ValueError('Unexpected contribution level')
            self.days[day] = level


def render(page):
    calendar = Calendar()
    calendar.feed(page)
    if len(calendar.days) < 300:
        raise ValueError('Incomplete contribution calendar; refusing to publish')
    first = min(calendar.days)
    first -= timedelta(days=(first.weekday() + 1) % 7)
    colors = ['#161b22', '#312e81', '#5b21b6', '#8b5cf6', '#c4b5fd']
    cells = []
    for day, level in sorted(calendar.days.items()):
        column, row = divmod((day - first).days, 7)
        cells.append(
            f'<rect x="{22 + column * 14}" y="{48 + row * 14}" width="11" '
            f'height="11" rx="2" fill="{colors[level]}">'
            f'<title>{day}: contribution intensity {level}/4</title></rect>'
        )
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 170" '
            'role="img" aria-labelledby="title desc"><title id="title">'
            'RayQCodes contribution activity</title><desc id="desc">'
            'Public GitHub contribution calendar. Brighter purple means higher activity. '
            'Updated by the daily Contribution snake workflow.</desc>'
            '<rect width="800" height="170" rx="10" fill="#0d1117"/>'
            '<text x="22" y="28" fill="#a78bfa" font-family="sans-serif" '
            'font-size="16">Public contribution activity · past year</text>'
            + ''.join(cells) + '</svg>\n')


if __name__ == '__main__':
    request = Request('https://github.com/users/RayQCodes/contributions',
                      headers={'User-Agent': 'RayQCodes-profile'})
    with urlopen(request, timeout=30) as response:
        svg = render(response.read().decode('utf-8'))
    Path('dist').mkdir(exist_ok=True)
    Path('dist/contribution-activity.svg').write_text(svg)
