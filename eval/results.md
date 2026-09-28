# Evaluation results

Run on 2026-09-28 against `doi_absence_and_leave_handbook.pdf` with 30 questions (21 answerable, 9 unanswerable). Answers are judged by gpt-4o-mini, citations are checked against the expected pages (two-page questions need both).

## Summary

| Metric | Result |
|---|---|
| Answer accuracy (all 30) | 97% |
| Answer accuracy (answerable) | 95% |
| Citation accuracy (answerable) | 90% |
| Refusal accuracy (unanswerable) | 100% |
| False refusals (answerable) | 0 of 21 |

## By question group

| Group | Description | Correct |
|---|---|---|
| base | Base set, direct questions | 20 of 20 |
| paraphrase | Paraphrased wording | 3 of 3 |
| two-page | Needs two pages | 2 of 3 |
| near-topic | Unanswerable, close to the handbook topic | 4 of 4 |

## Per question

| # | Group | Type | Question | Correct | Citation | Refused | Pages cited |
|---|---|---|---|---|---|---|---|
| 1 | base | answerable | How many vacation days do new employees get? | yes | yes | no | 7 |
| 2 | base | answerable | How much annual leave can an employee working in the United States carry over into the next leave year? | yes | yes | no | 7 |
| 3 | base | answerable | How many hours of sick leave do most employees earn each pay period? | yes | yes | no | 11 |
| 4 | base | answerable | How much sick leave can an employee use each leave year to care for a family member with a serious health condition? | yes | yes | no | 11 |
| 5 | base | answerable | Can an employee use sick leave to take care of an ill pet? | yes | yes | no | 12 |
| 6 | base | answerable | What is the maximum amount of sick leave a supervisor may advance to a full-time employee? | yes | yes | no | 12 |
| 7 | base | answerable | How many days of military funeral leave may an employee receive? | yes | yes | no | 13 |
| 8 | base | answerable | For how long can an employee who enters active military duty continue their FEHB enrollment? | yes | yes | no | 13 |
| 9 | base | answerable | How many weeks of unpaid leave is an employee entitled to under the Family and Medical Leave Act during a 12-month period? | yes | yes | no | 15 |
| 10 | base | answerable | How many months of federal service must an employee have completed to be eligible under Title II of FMLA? | yes | yes | no | 16 |
| 11 | base | answerable | How many weeks of FMLA leave can an employee take to care for a service member with a serious injury incurred on active duty? | yes | yes | no | 16 |
| 12 | base | answerable | How long can an employee be excused from duty to donate blood? | yes | yes | no | 25 |
| 13 | base | answerable | How many days of excused absence per calendar year may an employee use to serve as an organ donor? | yes | yes | no | 26 |
| 14 | base | answerable | How many days of excused absence do employees returning from military active duty receive? | yes | yes | no | 26 |
| 15 | base | answerable | Within how many work days must the SHRO notify an applicant whether their Voluntary Leave Transfer Program application was approved? | yes | yes | no | 20 |
| 16 | base | unanswerable | What is the annual salary of a GS-7 employee at the Department of the Interior? | yes | n/a | yes | - |
| 17 | base | unanswerable | What is the dress code for Department of the Interior employees? | yes | n/a | yes | - |
| 18 | base | unanswerable | How many paid federal holidays are there each year? | yes | n/a | yes | - |
| 19 | base | unanswerable | What is the daily per diem rate for official travel to Washington, DC? | yes | n/a | yes | - |
| 20 | base | unanswerable | Who won the 1998 FIFA World Cup? | yes | n/a | yes | - |
| 21 | paraphrase | answerable | If I have worked for the government for ten years, how fast does my leave build up? | yes | yes | no | 7 |
| 22 | paraphrase | answerable | Is there a cap on how much sick leave I can bank from one year to the next? | yes | yes | no | 11 |
| 23 | paraphrase | answerable | I am going to be a bone marrow donor. How much time off do I get for that without using my own leave? | yes | yes | no | 26 |
| 24 | two-page | answerable | How many hours of annual leave and how many hours of sick leave does a full-time employee with less than 3 years of service earn each pay period? | yes | yes | no | 11, 7 |
| 25 | two-page | answerable | How much annual leave can employees carry over into the next leave year inside and outside the United States, and what home leave benefit is tied to the overseas figure? | yes | no | no | 7 |
| 26 | two-page | answerable | What is the difference between an excused absence and administrative leave? | no | no | no | 29, 28 |
| 27 | near-topic | unanswerable | How many hours of annual leave do Department of Defense civilian employees earn per pay period? | yes | n/a | yes | - |
| 28 | near-topic | unanswerable | What is the sick leave accrual rate for State of California employees? | yes | n/a | yes | - |
| 29 | near-topic | unanswerable | How many weeks of paid parental leave do federal employees get under the Federal Employee Paid Leave Act? | yes | n/a | yes | - |
| 30 | near-topic | unanswerable | How many hours of religious compensatory time may an employee accumulate? | yes | n/a | yes | - |
