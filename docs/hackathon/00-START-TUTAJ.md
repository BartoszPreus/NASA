# NASA Space Apps Challenge 2026: Poznań · drużyna Zodiak
**14–15.11.2026 · +Jeden, ul. Za Bramką 1, Poznań** · temat roku: „The Next Frontier”

## Najważniejsze w 30 sekund
- **Start hakowania: sob 11:00.** Mentoring 1:1: sob 15:00. Pitch Doctors: ndz 10:30.
- **TWARDY DEADLINE: ndz 13:30**: zgłoszenie w portalu plus slajdy na info desk.
- **Pitch: ndz od 14:30, 3 min + 2 min Q&A** przed jury. Gala o 18:00.
- Do portalu NASA potrzebne jest osobne **demo: ≤7 slajdów ALBO wideo ≤30 s**. Przekroczenie limitu oznacza dyskwalifikację z Global Judging.
- Wszystko **po angielsku**. **Min. 1 źródło danych NASA**, które musi być w rdzeniu rozwiązania (kryterium Relevance).
- Ocena 1–5 w pięciu kryteriach: **Impact, Creativity, Validity, Relevance, Presentation**.
- Użycie AI („SI”) opisujemy w formularzu. Obrazy i wideo z AI muszą mieć watermark, bez logo NASA.
- Wszyscy z Zodiaka muszą być w Local Event **Poznań** (nie na waitliście).

## Shortlista (z naszej wcześniejszej oceny)
1. **Field Shift**: narzędzie do płodozmianu dla rolników. Dużo danych, część tylko z USA, dla PL: Sentinel-2, ERA5, SMAP, NASA POWER.
2. **Dancing with the SARs**: aplikacja do zmian powierzchni z NISAR. Pitch eko/klimat, np. osiadanie terenu albo powodzie w PL.
3. ➕ **Earth System Trend Detective**: szeregi czasowe plus test Mann-Kendall. Czysty Python, łatwe do domknięcia w 26 h.
- ❓ SPHEREx (niepewne). ❌ gry, Martian Map, Lunar Navigator, health monitoring.

## Struktura folderu
```
00-START-TUTAJ.md              ← ten plik
01-Poznan-event/               harmonogram, miejsce, Local Lead
02-Wyzwania/                   wszystkie 14 wyzwań + shortlista/ (pełne opisy + linki do danych)
03-Zasady-i-zgloszenie/        checklista zgłoszenia, kryteria oceny, nagrody, FAQ
04-Z-maila/                    co przyszło na Gmail (rejestracja, Zodiak, Poznań)
05-Harness/                    przewodnik po harnessie agentów (z poprzedniego hackathonu)
```

## Harness z START Warsaw: co zmienić pod ten hackathon
Harness (`projekty\start-warsaw-hackathon`) był ustawiony pod tamtą noc: hook kontekstu liczy „czas do 11:00”, a w RUNBOOK są checkpointy 01:00/04:00/07:00. Tutaj:
- deadline to **ndz 13:30** (a nie 11:00), więc trzeba przestawić godzinę w hooku kontekstu i w RUNBOOK,
- `/kickoff` dostaje treść wybranego wyzwania z `02-Wyzwania/shortlista/…`,
- `/pitch` ma dwa tryby: **3 min na scenę** i **7 slajdów do portalu**,
- `/demo-check` warto zrobić np. sob 19:00 (Evening Sprint), ndz 9:30 i ndz 12:00.

## Kontakty
- Local Lead: **Rahaf Zorba**, rahafzorba2002@gmail.com
- Zgłoszenia naruszeń: conduct@spaceappschallenge.org · ogólne: info@spaceappschallenge.org
- Space Apps Connect (forum, eksperci SME): link na górze strony spaceappschallenge.org

## Źródła
- Event Poznań: https://www.spaceappschallenge.org/2026/local-events/poznan/
- Wyzwania: https://www.spaceappschallenge.org/2026/challenges/
- Project Submission Guide: https://www.spaceappschallenge.org/resources/project-submission-guide/
- Judging & Awards Guide: https://www.spaceappschallenge.org/resources/judging-awards-guide/
- Participant FAQs: https://www.spaceappschallenge.org/resources/participant-faqs/
