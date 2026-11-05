#!/usr/bin/env python3
"""Authoring source for the long-form video 'Triple H: full story' -> longform/2026-11-05-triple-h.json

Markup in "say": [[caption text|spoken text]]  (captions show the first part, the voice speaks the second).
A beat without "show" continues the previous scene. "pause" = silence after the beat (s).
slot="Rxx" on a beat = real footage Ayaz saves into the Drive folder "WWE Triple H" (see the shot list).

Main sources (two per fact): WWE.com (title history "13 reigns of Triple H", show results, Hall of Fame 2019/2025,
health update Sept 8 2021, WrestleMania 38 boots article); corporate.wwe.com (Performance Center Jul 11 2013,
CCO Sept 6 2022, WM43 Riyadh Sept 12 2025, WM42 attendance Apr 22 2026); ESPN (25 years in WWE; First Take
retirement Mar 25 2022; DX Hall of Fame); Sports Illustrated (Sept 8 2021; Mar 25 2022; Jul 25 2022; WM43);
Wrestling Inc (Curtain Call consequences, WCW 1994, title wins); F4W/Wrestling Observer (KOTR 1997, Curtain Call,
HOF 2025 inductors); PWTorch (Raw Sept 2 2002); Bleacher Report; Philadelphia Inquirer (WrestleMania recaps);
Fightful (Tokyo live event Jun 29 2019; WCW exit); 411Mania (Triple H on why he left WCW); BGCA (bodybuilding);
CBS Sports (WM42 move, DX HOF); Post Wrestling (ESPN deal Aug 6 2025); Yahoo/PWInsider + WrestleTalk (new
contract, Apr 2026); USA Network (marriage Oct 25 2003).
"""
import json
import os

C = "https://upload.wikimedia.org/wikipedia/commons/"
M = {
    "nashua": C + "6/6b/Nashua_NH_Main_Street_50.JPG",
    "ring": C + "e/e3/Wrestling_ring.jpg",
    "atlanta": C + "b/b6/CNN_Center%2C_Atlanta%2C_Georgia.jpg",
    "msg": C + "4/4b/Madison_Square_Garden_%28MSG%29_-_Full_%2848124330357%29.jpg",
    "norfolk": C + "f/f1/Norfolk_Scope.jpg",
    "wellsfargo": C + "5/50/Wells_Fargo_Center_-_2019_OWL_Grand_Finals.jpg",
    "cntower": C + "2/2d/Toronto_-_ON_-_CN_Tower_bei_Nacht2.jpg",
    "theater": C + "5/53/Empty_Movie_Theater_Seats_%2854279616742%29.jpg",
    "georgiadome": C + "3/3e/2013.01.26.110220_Georgia_Dome_Atlanta_Georgia.jpg",
    "hardrock": C + "a/a4/200127-H-PX819-0092_-_49451830343.jpg",
    "superdome": C + "7/75/Caesars_Superdome_New_Orleans%2C_LA.jpg",
    "cowboys": C + "5/52/Cowboys_Stadium_full_view.jpg",
    "metlife": C + "b/b4/MetLife_Stadium_exterior_Super_Bowl_XLVIII.jpg",
    "nyse": C + "7/71/Sign_of_the_New_York_Stock_Exchange%2C_Broad_Street.jpg",
    "allegiant": C + "4/41/Allegiant_Stadium%2C_Las_Vegas%2C_Nevada_%2852259481401%29.jpg",
    "gym": C + "7/79/Colorful_pile_of_dumbbells_at_the_gym_2.jpg",
    "malden": C + "f/fd/Pleasant_Street%2C_Malden_MA.jpg",
    "hampton": C + "f/f7/Hampton_Coliseum_%2821285773232%29.jpg",
    "hartford": C + "8/8e/XL-Center-12-10-22-5.jpg",
    "sanjose": C + "d/da/SAP_Center_in_San_Jose_%2852194580276%29.jpg",
    "nassau": C + "f/f2/Nassau_Coliseum_2021.jpg",
    "sleepyhollow": C + "c/cf/Sleepy_Hollow%2C_New_York_%282010%29.jpg",
    "kemper": C + "9/96/Kemper_Arena_11-22-14.jpg",
    "reliant": C + "1/16/NRG_Stadium%2C_Houston%2C_Texas%2C_United_States.jpg",
    "levis": C + "d/d2/Levi%27s_Stadium_interior_1.jpg",
    "amway": C + "9/9f/Amway_Center.jpg",
    "barclays": C + "1/1e/Barclays_Center_2024.jpg",
    "jeddah": C + "6/68/Jawhara_Stadium.jpg",
    "riyadh": C + "9/98/Riyadh_Skyline_showing_the_King_Abdullah_Financial_District_%28KAFD%29_and_the_famous_Kingdom_Tower_.jpg",
    "stamford": C + "b/bf/Stamford_Connecticut_Skyline_Aug_2017.jpg",
    "staples": C + "9/9f/Staples_Center_in_2006.jpg",
}

B = []


def b(say, show=None, pause=None, slot=None):
    d = {"say": say}
    if show is not None:
        d["show"] = dict(show)
        if slot:
            d["show"]["slot"] = slot
    elif slot:
        raise ValueError(f"slot {slot} on a beat without a scene: {say[:40]}")
    if pause is not None:
        d["pause"] = pause
    B.append(d)


def chapter(n, title, years, spoken=None):
    said = f"[[{title}|{spoken}]]" if spoken else title
    b(f"Chapter {['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'][n]}. {said}.",
      {"type": "chapter", "num": n, "title": title, "kicker": years}, pause=0.6)


def photo(key, kicker=None, text=None, fit=None, **kw):
    d = {"type": "photo", "src": M[key]}
    if text:
        d["label"] = {"kicker": kicker or "", "text": text}
    if fit:
        d["fit"] = fit
    d.update(kw)
    return d


def head(kicker, text, sub=None, bg=None):
    d = {"type": "headline", "kicker": kicker, "text": text}
    if sub:
        d["sub"] = sub
    if bg:
        d["bg"] = M[bg]
    return d


def stmt(text, kicker=None, bg=None):
    d = {"type": "statement", "text": text}
    if kicker:
        d["kicker"] = kicker
    if bg:
        d["bg"] = M[bg]
    return d


def stat(kicker, value, sub, prefix="", suffix="", decimals=0, source=None, bg=None):
    d = {"type": "stat", "kicker": kicker, "value": value, "prefix": prefix, "suffix": suffix,
         "decimals": decimals, "sub": sub}
    if source:
        d["source"] = source
    if bg:
        d["bg"] = M[bg]
    return d


def vs(left, right, kicker, sub, bg=None):
    d = {"type": "versus", "left": left, "right": right, "kicker": kicker, "sub": sub}
    if bg:
        d["bg"] = M[bg]
    return d


def lst(kicker, items, title=None, bg=None):
    d = {"type": "list", "kicker": kicker, "items": items}
    if title:
        d["title"] = title
    if bg:
        d["bg"] = M[bg]
    return d


def quote(text, by, bg=None):
    d = {"type": "quote", "text": text, "by": by}
    if bg:
        d["bg"] = M[bg]
    return d


def tl(a, z, frm, to, label, kicker):
    return {"type": "timeline", "axis": [a, z], "from": frm, "to": to, "label": label, "kicker": kicker}


WWF, WCW, WWE, DX = "[[WWF|W W F]]", "[[WCW|W C W]]", "[[WWE|W W E]]", "[[DX|D X]]"

# ------------------------------------------------------------------ COLD OPEN
b("On [[May 19, 1996|May nineteenth, nineteen ninety-six]], four friends hugged in the middle of the ring at "
  "Madison Square Garden. Only one of them was punished for it.",
  head("May 19, 1996 · Madison Square Garden", "Four friends. *One* punished."), slot="R01")
b(f"Two of them were leaving for {WCW}, the rival company. One of them was the champion. "
  "The fourth was a young wrestler called Hunter Hearst Helmsley.",
  stmt("The fourth one was a *rookie*."), slot="R01")
b("He had been planned to win the King of the Ring that summer. Instead, the crown went to Stone Cold Steve Austin, "
  "and Austin [[3:16|three sixteen]] was born.",
  head("June 1996", "His crown went to *Stone Cold*"))
b(f"Twenty-six years later, the punished rookie was running the creative side of {WWE}.",
  tl(1996, 2022, 1996.38, 2022.56, "Head of WWE creative", "Twenty-six years"), slot="R03")
b("In between, he won fourteen world championships, tore both of his quadriceps, built a whole new brand, "
  "and married the boss's daughter.",
  lst("In between", ["14 world championships", "Both quadriceps torn", "Built NXT", "Married the boss's daughter"]),
  slot="R59")
b("And then a problem with his heart ended his wrestling career.",
  stmt("Then his *heart* ended it."))
b("This is the full story of Triple H. The bodybuilder from New Hampshire who became the leader of D-Generation X, "
  f"and then the man who decides what happens on {WWE} television. "
  "How he started, how he got famous, everything he won, why he stopped, and what he is doing right now, "
  "at the end of [[2026|twenty twenty-six]].",
  {"type": "title", "kicker": "The full story", "text": "Triple *H*", "sub": "1969 — 2026"}, pause=0.8,
  slot="R58")

# ------------------------------------------------------------------ 1
chapter(1, "The kid from Nashua", "1969 — 1992")
b("He was born Paul Michael Levesque, on [[July 27, 1969|July twenty-seventh, nineteen sixty-nine]], "
  "in Nashua, New Hampshire.",
  photo("nashua", "Nashua, New Hampshire", "Born *July 27, 1969*", fit="frame"))
b("Nashua is a small city about forty miles north of Boston. It is not a wrestling town.",
  {"type": "map", "kicker": "A New England start",
   "view": [-74.6, -69.9, 40.5, 43.6],
   "points": [["Nashua", 42.765, -71.468], ["Malden", 42.425, -71.066], ["Boston", 42.360, -71.058],
              ["Providence", 41.824, -71.413], ["Hartford", 41.764, -72.685], ["New York", 40.713, -74.006]]})
b("But Paul was a wrestling fan, and the wrestlers he watched on [[TV|T V]] in the [[1980s|nineteen eighties]] "
  "had one thing in common. They were huge.",
  stmt("The wrestlers on TV were *huge*.", bg="ring"))
b("So at fourteen, he started lifting weights.",
  photo("gym", "Age 14", "He starts *lifting*"), slot="R04")
b("He took it seriously. In [[1988|nineteen eighty-eight]], at nineteen, he won the title of "
  "Mister Teenage New Hampshire.",
  head("1988 · Age 19", "Mr. Teenage *New Hampshire*"), slot="R04")
b("He went to work at a Gold's Gym in Nashua, and he became one of its managers.",
  head("Nashua", "Managing a *gym*", "a bodybuilder with a plan"), slot="R04")
b("Through the powerlifter Ted Arcidi, he was introduced to a wrestling legend. Walter Kowalski. "
  "Killer Kowalski. One of the most feared villains of the [[1950s|nineteen fifties]] and sixties.",
  head("The teacher", "*Killer* Kowalski", "one of the great villains of the 1950s and '60s"))
b("Kowalski ran a wrestling school in Malden, just outside Boston. Paul signed up.",
  photo("malden", "Malden, Massachusetts", "Killer Kowalski's *school*"))
b("In March [[1992|nineteen ninety-two]], he wrestled his first match. His ring name was Terra Ryzing.",
  head("March 1992", "Debut: *Terra Ryzing*"), slot="R05")
b("Say it out loud. Terra Ryzing. Terror rising.",
  stmt("Terra Ryzing. *Terror rising.*"))
b("It was not a great name. But within two years, it got him a job with one of the two biggest wrestling "
  "companies in America.", pause=0.8)

# ------------------------------------------------------------------ 2
chapter(2, "The French aristocrat", "1994 — 1995")
b("In early [[1994|nineteen ninety-four]], World Championship Wrestling, Ted Turner's company in Atlanta, "
  "gave him a tryout match. It aired in February, and it earned him a one-year contract.",
  photo("atlanta", "WCW · Atlanta", "A *one-year* deal"), slot="R05")
b("Then the company noticed his last name.",
  stmt("Then they noticed his *last name*."))
b("Levesque sounded French. So by the summer, he was Jean-Paul Lévesque, a snobbish French aristocrat.",
  head("WCW · 1994", "Jean-Paul *Lévesque*", "a French aristocrat"), slot="R05")
b("He was paired with Lord Steven Regal, later known as William Regal, "
  "and the two became friends.",
  head("WCW · 1994", "With Lord Steven *Regal*", "the start of a long friendship"))
b("Then, in January [[1995|nineteen ninety-five]], he left.",
  stmt("January 1995. He *left*."))
b(f"The story usually told is that {WCW} would not give him a push as a singles wrestler. "
  "Triple H has called that false. He has said it really came down to money, and the length of the contract.",
  lst("Why he left WCW", ["The usual story: no singles push", "His version: the money", "and the length of the deal"]))
b(f"Either way, he went to the other company. The World Wrestling Federation, and Vince McMahon.",
  stmt("He went to *Vince McMahon*."))
b("Vince kept the rich snob. He just moved him from France to Connecticut.", pause=0.8)

# ------------------------------------------------------------------ 3
chapter(3, "The Curtain Call", "1995 — 1996")
b(f"In the {WWF}, he became Hunter Hearst Helmsley, an arrogant blue blood from Connecticut.",
  head("WWF · 1995", "Hunter Hearst *Helmsley*", "the Connecticut blue blood"), slot="R06")
b("He was introduced with short videos about etiquette and good manners.",
  stmt("Lessons in *etiquette*."), slot="R06")
b("His first [[TV|T V]] match aired on [[April 30, 1995|April thirtieth, nineteen ninety-five]]. "
  "He beat Buck Zumhofe.",
  vs("Hunter Hearst Helmsley", "Buck Zumhofe", "April 30, 1995", "his first WWF TV match"), slot="R06")
b("Backstage, he became close friends with Shawn Michaels, Kevin Nash, Scott Hall and Sean Waltman. "
  "The group became known as the Kliq.",
  lst("The Kliq", ["Shawn Michaels", "Kevin Nash — Diesel", "Scott Hall — Razor Ramon",
                   "Sean Waltman — the 1-2-3 Kid", "Hunter Hearst Helmsley"]))
b(f"In the spring of [[1996|ninety-six]], Hall and Nash were leaving for {WCW}. Their last night was a show at "
  "Madison Square Garden that was not on television. May nineteenth.",
  photo("msg", "Madison Square Garden", "*May 19, 1996*"), slot="R01")
b("After the main event, Michaels, the champion and a hero, hugged Nash, the villain he had just fought. "
  "Then Hall came out, and then Helmsley. Two heroes and two villains, celebrating together in the ring.",
  head("The Curtain Call", "Heroes and villains, *hugging*"), slot="R01")
b("Today, that sounds harmless. In [[1996|nineteen ninety-six]], it broke the biggest rule in wrestling. "
  "You never let the audience see that the enemies are friends.",
  stmt("It broke wrestling's *biggest rule*."))
b("Michaels was the champion. Hall and Nash were gone. That left one man to take the blame.",
  stmt("One man took the *blame*."))
b("Helmsley had been planned to win the King of the Ring tournament that June. The plan was scrapped.",
  head("June 1996", "The crown is *taken away*"))
b("Stone Cold Steve Austin won it instead, and his Austin [[3:16|three sixteen]] speech made him a star.",
  head("King of the Ring 1996", "The winner: *Stone Cold*", "Austin 3:16 is born"))
b("He was pushed down the card for months. He has said that when he asked Vince McMahon why only he was "
  "punished, he was told the punishment was what it was.",
  stmt("The punishment was *what it was*."), pause=0.8)

# ------------------------------------------------------------------ 4
chapter(4, "Earning it back", "1996 — 1997")
b("He kept working. By the fall, it was over.",
  stmt("He kept *working*."))
b("On [[October 21, 1996|October twenty-first, nineteen ninety-six]], on Raw, in Fort Wayne, Indiana, "
  "he beat Marc Mero for the Intercontinental Championship, with some help from a Mister Perfect chair shot.",
  vs("Helmsley", "Marc Mero", "Raw · Oct 21, 1996", "his first Intercontinental title"), slot="R07")
b("In February [[1997|ninety-seven]], he got a bodyguard. A powerful woman who had also trained at "
  "Killer Kowalski's school. Her name was Chyna.",
  head("February 1997", "Enter *Chyna*", "his bodyguard"), slot="R07")
b("On [[June 8, 1997|June eighth, nineteen ninety-seven]], in Providence, Rhode Island, he finally won the "
  "King of the Ring. One year late. He beat Mankind in the final.",
  vs("Helmsley", "Mankind", "King of the Ring 1997 · Providence", "the crown, one year late"), slot="R07")
b("By then, his long name was getting shorter. Hunter Hearst Helmsley became H H H. "
  "And then, simply, Triple H.",
  head("1997", "H.H.H. → *Triple H*"))
b("He had a crown and a new name. What he needed now was a crew. "
  "And his best friend was about to start one.", pause=0.8)

# ------------------------------------------------------------------ 5
chapter(5, "D-Generation X", "1997 — 1998", spoken="D Generation X")
b("In August [[1997|ninety-seven]], he started teaming with Shawn Michaels, with Chyna at their side.",
  head("August 1997", "Helmsley and *Michaels*"), slot="R08")
b("On Raw, on [[October 13, 1997|October thirteenth]], Michaels gave the group a name. D-Generation X. "
  "The veteran Rick Rude joined them as their insurance policy.",
  head("Oct 13, 1997", "*D-Generation X*", "Michaels · Helmsley · Chyna · Rick Rude"), slot="R08")
b(f"{DX} were rude, crude and proud of it. They mocked their opponents, their bosses and their own company. "
  "And a lot of young fans loved them for it.",
  lst("DX", ["Crude jokes", "Mocking the bosses", "Mocking their own company"]), slot="R08")
b("Then, at WrestleMania [[XIV|fourteen]], in March [[1998|ninety-eight]], Michaels lost the title to Stone Cold. "
  "His back was badly hurt, and he would not wrestle again for more than four years.",
  head("WrestleMania XIV", "Michaels is *gone*", "a back injury · out for more than four years"))
b("The next night, on Raw, Triple H said Michaels had dropped the ball. And he took over.",
  stmt("'He dropped the ball.' *Triple H takes over.*"))
b("He brought in X-Pac, his old Kliq friend Sean Waltman, and the New Age Outlaws, Road Dogg and Billy Gunn. "
  "The new D-Generation X was his.",
  lst("The new DX", ["Triple H", "Chyna", "X-Pac", "Road Dogg", "Billy Gunn"]), slot="R08")
b(f"On [[April 27, 1998|April twenty-seventh, nineteen ninety-eight]], Raw was in Hampton, Virginia. "
  f"{WCW}'s Monday Nitro was nearby, at the Norfolk Scope.",
  photo("hampton", "Raw · Hampton, Virginia", "*April 27, 1998*"))
b(f"So {DX} rode a military vehicle to the Nitro arena, and taunted {WCW} from outside, with cameras rolling. "
  "The doors stayed shut.",
  photo("norfolk", "Nitro · Norfolk Scope", "DX *invades*"), slot="R09")
b("It became one of the most famous moments of the Monday Night War.",
  stmt("A Monday Night War *classic*."), slot="R09")
b("At SummerSlam, on [[August 30, 1998|August thirtieth]], at Madison Square Garden, he beat The Rock "
  "in a ladder match for the Intercontinental title.",
  vs("Triple H", "The Rock", "SummerSlam 1998 · ladder match", "Triple H wins the Intercontinental title"),
  slot="R10")
b("Two years after the Curtain Call, the same building was cheering for him. "
  "But Triple H was about to stop caring whether anyone cheered.", pause=0.8)

# ------------------------------------------------------------------ 6
chapter(6, "The Game", "1999 — 2000")
b("At WrestleMania [[XV|fifteen]], in Philadelphia, he turned on his friend X-Pac, and joined "
  "Vince McMahon's Corporation.",
  photo("wellsfargo", "WrestleMania XV · Philadelphia", "He turns on *DX*"))
b("He became The Game, a nickname he has said he made up during an interview with Jim Ross.",
  head("1999", "*The Game*", "a line he made up in an interview"))
b("On [[August 23, 1999|August twenty-third, nineteen ninety-nine]], on Raw, in Ames, Iowa, he beat Mankind, "
  f"with Shane McMahon as the referee. He was the {WWF} Champion for the first time.",
  head("Raw · Aug 23, 1999", "WWF Champion *No. 1*", "beat Mankind in Ames, Iowa"), slot="R11")
b("Then he went after the McMahon family itself. In November, Vince's daughter, Stephanie, "
  "was about to marry the wrestler Test, on Raw.",
  head("Nov 29, 1999", "A *wedding* on Raw"), slot="R12")
b("Triple H interrupted with a video. In the storyline, he had already married her, at a drive-thru chapel "
  "in Las Vegas.",
  stmt("He had *already* married her."), slot="R12")
b("At Armageddon, on [[December 12, 1999|December twelfth]], he beat Vince McMahon. "
  "And Stephanie turned on her father, and stood with her husband.",
  vs("Triple H", "Vince McMahon", "Armageddon 1999", "Stephanie turns on her father"), slot="R12")
b("For most of the next year, the two of them ran the company on television. "
  "It became known as the McMahon-Helmsley Era.",
  head("2000", "The McMahon-Helmsley *Era*"))
b("And he became one of the best villains in wrestling. On [[February 27, 2000|February twenty-seventh, "
  "two thousand]], in Hartford, Connecticut, he faced Cactus Jack inside Hell in a Cell. "
  "If Mick Foley lost, he had to retire.",
  photo("hartford", "No Way Out 2000 · Hartford", "*Hell in a Cell* vs. Cactus Jack"), slot="R13")
b("Triple H won with the Pedigree, and Foley retired. For about five weeks.",
  stmt("Foley retired. For about *five weeks*."), slot="R13")
b("At WrestleMania [[2000|two thousand]], in Anaheim, he kept the title against The Rock, Big Show "
  "and Mick Foley, with a McMahon in every corner. For once, the villain closed WrestleMania as the winner.",
  lst("WrestleMania 2000", ["Fatal four-way elimination", "A McMahon in every corner",
                            "Triple H eliminates The Rock last", "The villain leaves as champion"]), slot="R14")
b("By now, his entrance was famous too. A mouthful of water, spat into the lights. "
  "And from [[2001|two thousand one]], a theme song recorded by Motörhead, called The Game.",
  head("The entrance", "Water. Lights. *The Game.*", "theme by Motörhead, from 2001"), slot="R58")
b("On [[May 21, 2000|May twenty-first, two thousand]], in Louisville, he beat The Rock for the title in a "
  "sixty-minute Iron Man match, six falls to five.",
  stat("Judgment Day 2000 · Iron Man match", 60, "minutes — Triple H wins, 6 falls to 5", suffix=" min"),
  slot="R15")
b("Remember that date. May twenty-first. Exactly one year later, on the same date, his body gave out.",
  stmt("May 21. *Remember that date.*"), pause=0.8)

# ------------------------------------------------------------------ 7
chapter(7, "Torn", "2001 — 2002")
b("In [[2001|two thousand one]], he teamed with his old enemy Stone Cold Steve Austin, as the Two-Man Power Trip, "
  "and they won the tag team titles.",
  head("2001", "The Two-Man *Power Trip*", "with Stone Cold · tag team champions"))
b("On [[May 21, 2001|May twenty-first, two thousand one]], on Raw, in San Jose, they defended those titles "
  "against Chris Jericho and Chris Benoit.",
  photo("sanjose", "Raw · San Jose", "*May 21, 2001*"), slot="R16")
b("Near the end, Triple H ran in to break up a submission hold, and his left quadriceps tore.",
  head("May 21, 2001", "A torn *quadriceps*", "his left leg"), slot="R16")
b("But he finished the match. He even let Jericho put him in the Walls of Jericho, "
  "on top of the announce table, on a torn leg.",
  stmt("He *finished* the match."), slot="R16")
b("He needed surgery, and he was out for eight months.",
  stat("2001 — 2002", 8, "months out after surgery", suffix=" mo"))
b("He came back on [[January 7, 2002|January seventh, two thousand two]], at Madison Square Garden. "
  "The building where the Curtain Call happened gave him a hero's welcome.",
  photo("msg", "Raw · Madison Square Garden", "*Jan 7, 2002*: the return"), slot="R17")
b("Less than two weeks later, in Atlanta, he won the Royal Rumble, throwing out Kurt Angle last.",
  head("Royal Rumble · Jan 20, 2002", "Rumble *winner*", "last man out: Kurt Angle"), slot="R18")
b("And at WrestleMania [[X8|ex eight]], on [[March 17, 2002|March seventeenth]], in front of more than "
  "[[68,000|sixty-eight thousand]] fans in Toronto, he beat Chris Jericho for the Undisputed Championship.",
  photo("cntower", "WrestleMania X8 · Toronto", "*Undisputed* champion"), slot="R18")
b("Ten months after the injury, he was on top again. And his company was about to change its name.", pause=0.8)

# ------------------------------------------------------------------ 8
chapter(8, "Evolution", "2002 — 2005")
b(f"That spring, after a legal fight with the World Wildlife Fund, the {WWF} became {WWE}. "
  "And the roster was divided into two brands, Raw and SmackDown.",
  head("2002", "The WWF becomes *WWE*", "two brands: Raw and SmackDown"))
b("That summer, his best friend came back. Shawn Michaels had not wrestled in more than four years. "
  "At SummerSlam, on [[August 25, 2002|August twenty-fifth]], they fought in an unsanctioned street fight.",
  vs("Shawn Michaels", "Triple H", "SummerSlam 2002", "Michaels' first match in more than four years"),
  slot="R20")
b("Michaels won. Their rivalry went on for years.",
  photo("nassau", "SummerSlam 2002 · Uniondale, New York", "A rivalry for *years*"), slot="R20")
b("About a week later, on [[September 2, 2002|September second]], on Raw, in Milwaukee, the general manager "
  "Eric Bischoff handed Triple H a brand new title. The World Heavyweight Championship. The big gold belt.",
  head("Sept 2, 2002", "The *World Heavyweight* title", "handed to him by Eric Bischoff"), slot="R19")
b("In early [[2003|two thousand three]], he formed a new group. Evolution. The legend Ric Flair, "
  "and two young wrestlers, Randy Orton and Batista.",
  lst("Evolution", ["Triple H", "Ric Flair — the legend", "Randy Orton — the future", "Batista — the muscle"]),
  slot="R21")
b("In real life, he and Stephanie McMahon had been dating since [[2000|two thousand]]. On [[October 25, 2003|October twenty-fifth, two thousand three]], "
  "they got married for real, in Sleepy Hollow, New York.",
  photo("sleepyhollow", "Sleepy Hollow, New York", "Married *Oct 25, 2003*"))
b("They have three daughters. Aurora, Murphy and Vaughn.",
  lst("The family", ["Aurora — 2006", "Murphy — 2008", "Vaughn — 2010"]))
b("In [[2004|two thousand four]], he tried Hollywood, as the vampire Jarko Grimwood in Blade: Trinity.",
  photo("theater", "2004", "*Blade: Trinity*"), slot="R23")
b("Meanwhile, Batista was getting too big to be anyone's sidekick. At WrestleMania [[21|twenty-one]], "
  "on [[April 3, 2005|April third, two thousand five]], in Los Angeles, he beat Triple H for the "
  "World Heavyweight title.",
  vs("Batista", "Triple H", "WrestleMania 21 · Los Angeles", "the student beats the teacher", bg="staples"), slot="R22")
b("Triple H had built the star who replaced him. It would not be the last time.", pause=0.8)

# ------------------------------------------------------------------ 9
chapter(9, "End of an era", "2006 — 2012")
b("In June [[2006|two thousand six]], he and Shawn Michaels brought back D-Generation X. "
  "Older, but not much more mature.",
  head("June 12, 2006", "*DX* is back"), slot="R24")
b("Then, on [[January 7, 2007|January seventh, two thousand seven]], in Kansas City, it happened again. "
  "He tore his other quadriceps. The right one.",
  photo("kemper", "New Year's Revolution · Kansas City", "The *other* quad"))
b("He came back at SummerSlam that August. Two torn quadriceps. Two comebacks.",
  stat("2001 · 2007", 2, "torn quadriceps — two comebacks", suffix="×"))
b(f"In [[2009|two thousand nine]], he closed WrestleMania [[25|twenty-five]] in Houston, beating Randy Orton "
  f"to keep the {WWE} Championship.",
  photo("reliant", "WrestleMania 25 · Houston", "Main event vs. *Randy Orton*"), slot="R25")
b("Then he took on the one man nobody could beat at WrestleMania. The Undertaker.",
  stmt("The one man nobody beat at *WrestleMania*."))
b("At WrestleMania [[27|twenty-seven]], in Atlanta, in [[2011|twenty eleven]], Triple H tried to end the "
  "Undertaker's winning streak, in a No Holds Barred match. He lost. The streak went to nineteen and oh.",
  photo("georgiadome", "WrestleMania 27 · Atlanta", "The Streak: *19–0*"), slot="R26")
b("A year later, in Miami, they went one more time, inside Hell in a Cell, with Shawn Michaels as the referee. "
  f"{WWE} called it the End of an Era.",
  photo("hardrock", "WrestleMania 28 · Miami", "*End of an Era*"), slot="R26")
b("The Undertaker won again. Twenty and oh. Afterwards, the three of them walked out together.",
  stmt("20–0. Then they walked out *together*."), slot="R26")
b("By then, he was spending more time in an office than in a ring. In August "
  "[[2011|twenty eleven]], he had become an executive vice president.",
  head("August 2011", "Executive *vice president*", "talent and live events"))
b(f"And he had a plan for the future of {WWE}.", pause=0.8)

# ------------------------------------------------------------------ 10
chapter(10, "The architect", "2012 — 2016")
b(f"{WWE}'s developmental brand was called [[NXT|N X T]]. From [[2012|twenty twelve]], it taped its shows at "
  "Full Sail University, near Orlando, and Triple H took charge of it.",
  head("2012 · Winter Park, Florida", "The home of *NXT*", "Full Sail University"), slot="R27")
b(f"On [[July 11, 2013|July eleventh, twenty thirteen]], {WWE} opened its Performance Center in Orlando. "
  "Twenty-six thousand square feet, and seven rings.",
  stat("WWE Performance Center · July 11, 2013", 7, "rings · 26,000 square feet", suffix=" rings"), slot="R27")
b("He signed wrestlers from the independent scene and from Japan, and gave them time to grow. "
  "By [[2014|twenty fourteen]], [[NXT|N X T]] had its own big events, called TakeOver.",
  lst("NXT under Triple H", ["Stars from the indies and Japan", "Time to grow", "TakeOver: May 29, 2014"]),
  slot="R27")
b("On television, he was a villain again. From SummerSlam [[2013|twenty thirteen]], he and Stephanie played "
  "The Authority, the bosses who held down anyone they did not like.",
  head("2013 — 2016", "*The Authority*", "Triple H and Stephanie McMahon"), slot="R28")
b("Their biggest target was Daniel Bryan. At WrestleMania [[30|thirty]], in New Orleans, Bryan beat Triple H in "
  "the opening match, and then won the title later that night.",
  vs("Daniel Bryan", "Triple H", "WrestleMania 30 · New Orleans", "Bryan wins — then wins the title"),
  slot="R28")
b("At WrestleMania [[31|thirty-one]], in Santa Clara, he came to the ring in a Terminator-themed entrance, "
  "and he beat Sting, in Sting's first match in a WWE ring.",
  photo("levis", "WrestleMania 31 · Santa Clara", "The *Terminator* entrance"), slot="R29")
b("And at the Royal Rumble in January [[2016|twenty sixteen]], in Orlando, he entered at number thirty, the last "
  "spot, and won the whole thing. The prize that night was the world title itself.",
  photo("amway", "Royal Rumble 2016 · Orlando", "Entrant *No. 30*"), slot="R30")
b("It was his fourteenth world championship.",
  stat("Jan 24, 2016", 14, "world championships", suffix="×"), slot="R30")
b("At WrestleMania [[32|thirty-two]], in Arlington, Texas, he lost it to Roman Reigns in the main event, "
  f"in front of a crowd {WWE} announced as [[101,763|one hundred and one thousand, seven hundred and sixty-three]].",
  photo("cowboys", "WrestleMania 32 · Arlington", "WWE's count: *101,763*"))
b("He was forty-six. He did not know it yet, but he had only a handful of big matches left.",
  pause=0.8)

# ------------------------------------------------------------------ 11
chapter(11, "The last bell", "2018 — 2022")
b("In April [[2018|twenty eighteen]], at WrestleMania [[34|thirty-four]], in New Orleans, he and Stephanie faced "
  "Kurt Angle and Ronda Rousey, in Rousey's first match. Rousey made Stephanie tap out.",
  photo("superdome", "WrestleMania 34 · New Orleans", "Ronda Rousey's *first match*"))
b("A year later, at WrestleMania [[35|thirty-five]], he beat his old Evolution partner Batista, "
  "in a No Holds Barred match. Batista retired after it.",
  photo("metlife", "WrestleMania 35 · East Rutherford, NJ", "Batista's *last match*"), slot="R31")
b(f"That same weekend, D-Generation X went into the {WWE} Hall of Fame. Triple H, Shawn Michaels, Road Dogg, "
  "Billy Gunn, X-Pac, and Chyna, who had died in [[2016|twenty sixteen]].",
  photo("barclays", "WWE Hall of Fame · April 6, 2019", "DX: *Hall of Famers*"), slot="R32")
b("In June [[2019|twenty nineteen]], in Jeddah, Saudi Arabia, he lost to Randy Orton at Super ShowDown. "
  "It was the last time he wrestled on television.",
  photo("jeddah", "Super ShowDown · Jeddah", "His last *televised* match"))
b("His real last match came three weeks later, at a show that was not televised, in Tokyo. On "
  "[[June 29, 2019|June twenty-ninth]], at the Ryogoku Sumo Hall, he and Shinsuke Nakamura beat Samoa Joe "
  "and Robert Roode.",
  head("Tokyo · June 29, 2019", "The *real* last match", "with Shinsuke Nakamura · Ryogoku Sumo Hall"))
b("Nobody knew it would be the last one.",
  stmt("Nobody knew it was the *last one*."))
b(f"In September [[2021|twenty twenty-one]], {WWE} announced that he had had a cardiac event, caused by a "
  "genetic heart issue, and a successful procedure at Yale New Haven Hospital.",
  head("Sept 8, 2021", "A *cardiac event*", "caused by a genetic heart issue"))
b("On [[March 25, 2022|March twenty-fifth, twenty twenty-two]], on ESPN's First Take, he revealed that he had a "
  "defibrillator in his chest. And he made it official.",
  head("March 25, 2022", "On ESPN's *First Take*"), slot="R33")
b("I will never wrestle again.",
  quote("I will never wrestle again.", "ESPN's First Take, March 25, 2022"), slot="R33")
b("Nine days later, on the second night of WrestleMania [[38|thirty-eight]], in Arlington, he walked out to open "
  "the show, took off his boots, and left them in the middle of the ring.",
  photo("cowboys", "WrestleMania 38 · Arlington", "He leaves his *boots*"), slot="R02")
b("Thirty years after Terra Ryzing, his wrestling career was over. His biggest job was about to begin.",
  pause=0.8)

# ------------------------------------------------------------------ 12
chapter(12, "The boss", "2022 — 2026")
b("In July [[2022|twenty twenty-two]], Vince McMahon retired, in the middle of an investigation by the "
  "company's board into his conduct.",
  head("July 22, 2022", "Vince McMahon *retires*", bg="stamford"))
b("The same day, the company announced that Triple H was coming back as its head of talent relations. "
  "Three days later, he took over creative.",
  head("July 25, 2022", "Triple H takes over *creative*"), slot="R34")
b(f"For the first time in about forty years, someone other than Vince McMahon was deciding what happened on "
  f"{WWE} television. In September, Triple H was named Chief Content Officer.",
  head("Sept 6, 2022", "Chief Content *Officer*"), slot="R34")
b(f"In September [[2023|twenty twenty-three]], {WWE} and the [[UFC|U F C]] came together in a new company, "
  "[[TKO|T K O]], on the New York Stock Exchange.",
  photo("nyse", "Sept 12, 2023", "WWE + UFC = *TKO*"))
b("Then Raw moved to Netflix. The first show was on [[January 6, 2025|January sixth, twenty twenty-five]], "
  "under a ten-year deal reported at more than five billion dollars.",
  stat("Raw on Netflix · from Jan 6, 2025", 5, "billion dollars over 10 years (reported)", prefix="$",
       suffix="B+"), slot="R34")
b(f"In April [[2025|twenty twenty-five]], in Las Vegas, he went into the {WWE} Hall of Fame again, this time on "
  "his own, as the headliner. The man who inducted him was Shawn Michaels.",
  head("April 18, 2025 · Las Vegas", "Hall of Fame *headliner*", "inducted by Shawn Michaels"), slot="R35")
b(f"That summer, {WWE} signed a five-year deal with [[ESPN|E S P N]] for its biggest events in the United States. "
  "And in September, Triple H announced that WrestleMania [[43|forty-three]] will be held in Riyadh, "
  "Saudi Arabia, in [[2027|twenty twenty-seven]]. The first WrestleMania outside North America.",
  photo("riyadh", "WrestleMania 43 · Riyadh, 2027", "The first outside *North America*"), slot="R36")
b("In April [[2026|twenty twenty-six]], WrestleMania [[42|forty-two]] went back to Las Vegas, and the company "
  "announced a two-night crowd of more than a hundred and six thousand.",
  photo("allegiant", "WrestleMania 42 · Las Vegas", "WWE's count: *106,072*"), slot="R03")
b("About a week later, reports said he had signed a new multi-year contract.",
  head("April 2026", "A new *multi-year* deal"), slot="R03")
b("Now look at what he left in the ring. Fourteen world championships. Nine WWE titles and five World "
  "Heavyweight titles. Five Intercontinental titles. Two European titles. Two Royal Rumble wins. "
  "The King of the Ring. And two trips into the Hall of Fame.",
  lst("Career", ["14× world champion (9 WWE · 5 World Heavyweight)", "5× Intercontinental Champion",
                 "2× European Champion", "Royal Rumble 2002 & 2016", "King of the Ring 1997",
                 "Hall of Fame: 2019 (DX) & 2025"]), slot="R59")
b("But his biggest legacy might be the people he built. The Performance Center, a new generation of stars, "
  "and the brand that trained them.",
  stmt("His legacy: the *people he built*."), slot="R59")
b("He was the rookie punished for one hug in [[1996|nineteen ninety-six]]. Today, he is the man who decides "
  "who gets the push.",
  head("The legacy", "From punished to *the boss*"), slot="R59")
b("And it all started with a kid in Nashua, lifting weights, because the wrestlers on [[TV|T V]] were huge.",
  head("Where it started", "A gym in *Nashua*"), slot="R59", pause=0.6)
b("The Undertaker's story is next on this channel. Subscribe, so you do not miss it.",
  {"type": "end", "kicker": "Next on the channel", "text": "The Undertaker: the *full story*",
   "cta": "Subscribe", "follow": "New WWE stories every week"})
b("And tell me in the comments. What is the greatest Triple H match of all time? Hell in a Cell with "
  "Cactus Jack, the street fight with Shawn Michaels, or the End of an Era?",
  {"type": "end", "kicker": "Your take", "text": "The greatest Triple H match *ever?*",
   "cta": "Tell us below ↓", "follow": "Subscribe for the next story"})

# ------------------------------------------------------------------ on-screen credit per slot
SLOT_CREDIT = {s: "WWE" for s in ("R01", "R02", "R03", "R04", "R06", "R07", "R08", "R09", "R10", "R11", "R12",
                                   "R13", "R14", "R15", "R16", "R17", "R18", "R19", "R20", "R21", "R22", "R24",
                                   "R25", "R26", "R27", "R28", "R29", "R30", "R31", "R32", "R34", "R35", "R36",
                                   "R58", "R59")}
SLOT_CREDIT.update({"R05": "WCW / WWE", "R23": "New Line Cinema", "R33": "ESPN", "R60": ""})
used = {x["show"]["slot"] for x in B if "show" in x and "slot" in x["show"]}
assert used <= set(SLOT_CREDIT), used - set(SLOT_CREDIT)

job = {
    "id": "2026-11-05-triple-h",
    "format": "longform",
    "title": "How Triple H Went From Punished to WWE Boss | Full Story",
    "voice": {"tts": "kokoro", "voice": "am_michael", "speed": 1.03},
    "music": {"gen": "ambient", "gain_db": -24},
    "thumbnail": {"kicker": "Triple H", "text": "Punished to *boss*", "sub": "The full story",
                  "slot": "R60", "sharp": True, "focus": [0.5, 0.22], "big": "14×"},
    "slot_credit": SLOT_CREDIT,
    "slot_in": {},
    "beats": B,
}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-triple-h.json")
json.dump(job, open(out, "w"), ensure_ascii=False, indent=1)


def spoken(s):
    import re
    return re.sub(r"\[\[[^|\]]*\|([^\]]*)\]\]", r"\1", s)


words = sum(len(spoken(x["say"]).split()) for x in B)
print(f"{len(B)} beats, ~{words} spoken words (~{words / 150:.1f} min), scenes: {sum(1 for x in B if 'show' in x)}, "
      f"footage slots: {len(used)}")
