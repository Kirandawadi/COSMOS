# flake8: noqa
xpath_mappings = {
    'Concat(xpath://*[@id="cpad"]/h2, xpath://*[@id="cpad"]/h3)': 'xpath://*[@id="cpad"]/h2 xpath://*[@id="cpad"]/h3',
    'Concat(xpath://*[@id="cpad"]/h2, doc.title)': 'xpath://*[@id="cpad"]/h2 {title}',
    'xpath://*[@id="cpad"]/h2': 'xpath://*[@id="cpad"]/h2',
    'xpath://*[@id="cpad"]/h3': 'xpath://*[@id="cpad"]/h3',
    'Concat("GCN ", xpath://*[@id="gcn-news-and-events"]/a)': 'GCN xpath://*[@id="gcn-news-and-events"]/a',
    'Concat("GCN", xpath://*[@id="super-kamioka-neutrino-detection-experiment-super-kamiokande"]/a)': 'GCN xpath://*[@id="super-kamioka-neutrino-detection-experiment-super-kamiokande"]/a',
    'concat("MAST - Missions and Data - ",xpath://*[@id="page-title"])': 'MAST - Missions and Data - xpath://*[@id="page-title"]',
    'concat("HEK Observation Details: ",xpath://*[@id="event-detail"]/div[1])': 'HEK Observation Details: xpath://*[@id="event-detail"]/div[1]',
    'concat("The Martian Meteorite Compendium ",xpath://*[@id="main_content_wrapper"]/h4/text())': 'The Martian Meteorite Compendium xpath://*[@id="main_content_wrapper"]/h4/text()',
    'concat("Antarctic Meteorite Sample Preparation - ",xpath://*[@id="main_content_wrapper"]/h4)': 'Antarctic Meteorite Sample Preparation - xpath://*[@id="main_content_wrapper"]/h4',
    'concat("My NASA Data: ",xpath://*[@id="block-mynasadata-theme-content"]/article/div/div[1]/h1/span)': 'My NASA Data: xpath://*[@id="block-mynasadata-theme-content"]/article/div/div[1]/h1/span',
    'concat("My NASA Data: Phenomenon - ",xpath:/html/body/div[1]/div/div[1]/div[2]/div/div[1]/div/section/div/div[1]/h1/text())': "My NASA Data: Phenomenon - xpath:/html/body/div[1]/div/div[1]/div[2]/div/div[1]/div/section/div/div[1]/h1/text()",
    'concat("My NASA Data: Mini Lessons - ",xpath://*[@id="block-mynasadata-theme-content"]/article/div/div[1]/h1/span)': 'My NASA Data: Mini Lessons - xpath://*[@id="block-mynasadata-theme-content"]/article/div/div[1]/h1/span',
    'concat("My NASA Data: Lesson Plans - ",xpath://*[@id="block-mynasadata-theme-content"]/article/div/div[1]/h1/span)': 'My NASA Data: Lesson Plans - xpath://*[@id="block-mynasadata-theme-content"]/article/div/div[1]/h1/span',
    'concat("My NASA Data: Interactive Models - ",xpath://*[@id="block-mynasadata-theme-content"]/article/div/div[1]/h1/span)': 'My NASA Data: Interactive Models - xpath://*[@id="block-mynasadata-theme-content"]/article/div/div[1]/h1/span',
    'concat("FIRMS Layer Information: ",xpath://*[@id="layerid"])': 'FIRMS Layer Information: xpath://*[@id="layerid"]',
    "concat(“Artwork: “, xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b)": "Artwork: xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b",
    "concat(“Calibration: “, xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b)": "Calibration: xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b",
    "concat(“Canyons: “, xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b)": "Canyons: xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b",
    "concat(“Craters: “, xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b)": "Craters: xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b",
    "concat(“Dust Storms: “, xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b)": "Dust Storms: xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b",
    "concat(“Martian Terrain: “, xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b)": "Martian Terrain: xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b",
    "concat(“Sand Dunes: “, xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b)": "Sand Dunes: xpath:/html/body/div/table/tbody/tr/td/table[7]/tbody/tr/td[3]/table[2]/tbody/tr[4]/td/p[1]/b",
    'concat(“MER Mission: “, xpath://*[@id="white-blur"]/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td[3]/table/tbody/tr[1]/td)': 'MER Mission: xpath://*[@id="white-blur"]/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td[3]/table/tbody/tr[1]/td',
    'concat(“MER Spacecraft: “, xpath://*[@id="white-blur"]/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td[3]/table/tbody/tr[1]/td)': 'MER Spacecraft: xpath://*[@id="white-blur"]/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td[3]/table/tbody/tr[1]/td',
    'concat(“MER Spotlight: “, xpath://*[@id="white-blur"]/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td[3]/table/tbody/tr[1]/td)': 'MER Spotlight: xpath://*[@id="white-blur"]/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td[3]/table/tbody/tr[1]/td',
    'concat(“MER Videos: “, xpath://*[@id="white-blur"]/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td[3]/table/tbody/tr[1]/td)': 'MER Videos: xpath://*[@id="white-blur"]/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td[3]/table/tbody/tr[1]/td',
    'concat(“Imagine Mars: “, xpath://*[@id="centeredcontent2"]/table[3]/tbody/tr/td/table/tbody/tr/td/table[1]/tbody/tr/td[2]/div)': 'Imagine Mars: xpath://*[@id="centeredcontent2"]/table[3]/tbody/tr/td/table/tbody/tr/td/table[1]/tbody/tr/td[2]/div',
    'concat(“Imagine Mars Webcasts: “, xpath://*[@id="centeredcontent2"]/table[4]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr[2]/td/div/p[1]/text()[1])': 'Imagine Mars Webcasts: xpath://*[@id="centeredcontent2"]/table[4]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr[2]/td/div/p[1]/text()[1]',
    'STEREO Learning Center - {xpath://*[@id="content"]/div/h3}': 'STEREO Learning Center - xpath://*[@id="content"]/div/h3',
    '{xpath://*[@id="content"]/div/h1}': 'xpath://*[@id="content"]/div/h1',
    "{xpath:/html/body/center[1]/font/h1/i}": "xpath:/html/body/center[1]/font/h1/i",
    "{xpath:/html/body/div[2]/section[1]/div/div/h5/text()} - Images": "xpath:/html/body/div[2]/section[1]/div/div/h5/text() - Images",
    "{xpath:/html/body/div[1]/div[2]/div/div[1]/div/div/div/div/div/h2/text()}": "xpath:/html/body/div[1]/div[2]/div/div[1]/div/div/div/div/div/h2/text()",
    "{xpath:/html/body/div[2]/div[2]/div/div[1]/div/div/div/div[1]/div/h2/text()}": "xpath:/html/body/div[2]/div[2]/div/div[1]/div/div/div/div[1]/div/h2/text()",
    "{xpath:/html/body/div[1]/div[2]/div/div[1]/div/div/div/div[1]/div/h2/text()}": "xpath:/html/body/div[1]/div[2]/div/div[1]/div/div/div/div[1]/div/h2/text()",
    '{xpath://*[@id="ascl_body"]/div/h2}': 'xpath://*[@id="ascl_body"]/div/h2',
    '{xpath://*[@id="rightcontent"]/h1} NASA - NSSDCA - Experiment - Details': 'xpath://*[@id="rightcontent"]/h1 NASA - NSSDCA - Experiment - Details',
    '{xpath://*[@id="rightcontent"]/h1} NASA - NSSDCA - Spacecraft - Details': 'xpath://*[@id="rightcontent"]/h1 NASA - NSSDCA - Spacecraft - Details',
    '{xpath://*[@id="rightcontent"]/h1} NASA - NSSDCA - Dataset - Details': 'xpath://*[@id="rightcontent"]/h1 NASA - NSSDCA - Dataset - Details',
    '{xpath://*[@id="rightcontent"]/h1} NASA - NSSDCA - Publication - Details': 'xpath://*[@id="rightcontent"]/h1 NASA - NSSDCA - Publication - Details',
    '{xpath://*[@id="contentwrapper"]/center/h2} - Abstract': 'xpath://*[@id="contentwrapper"]/center/h2 - Abstract',
    '{xpath://*[@id="contentwrapper"]/center/h1} - Publications and Abstracts': 'xpath://*[@id="contentwrapper"]/center/h1 - Publications and Abstracts',
    '{xpath://*[@id="page"]/section[3]/div/article/header/h2} - Blogs by Author': 'xpath://*[@id="page"]/section[3]/div/article/header/h2 - Blogs by Author',
    "{xpath:/html/body/h2} - {xpath:/html/body/h4[2]}": "xpath:/html/body/h2} - xpath:/html/body/h4[2]",
    "{title} - {xpath:/html/body/div/div/h2}": "{title} - xpath:/html/body/div/div/h2",
    "{title} - {xpath:/html/body/h3[1]}": "{title} - xpath:/html/body/h3[1]",
    '{title} - {xpath://*[@id="OneColumn"]/div[2]/table/tbody/tr/td/blockquote/h2}': '{title} - xpath://*[@id="OneColumn"]/div[2]/table/tbody/tr/td/blockquote/h2',
    '{title} - {xpath://*[@id="content-wrapper"]/h1}': '{title} - xpath://*[@id="content-wrapper"]/h1',
    "{xpath:/html/body/div/main/div[2]/section/div[2]/h1} | Astrobiology": "xpath:/html/body/div/main/div[2]/section/div[2]/h1 | Astrobiology",
    "{xpath:/html/body/div/main/section/div[2]/h1} | The Classroom | Astrobiology": "xpath:/html/body/div/main/section/div[2]/h1 | The Classroom | Astrobiology",
    "{xpath:/html/body/div/section[2]/div[1]/article/h1} | About FameLab - Finalist Bios": "xpath:/html/body/div/section[2]/div[1]/article/h1 | About FameLab - Finalist Bios",
    "{xpath:/html/body/div/section[2]/div[2]/h1} | About FameLab - Videos": "xpath:/html/body/div/section[2]/div[2]/h1 | About FameLab - Videos",
    '{xpath://*[@id="container-body"]/div[2]/div[2]/h2} - {xpath://*[@id="container-body"]/div[2]/div[2]/h4/span[1]/text() | NASA Astrobiology Institute': 'xpath://*[@id="container-body"]/div[2]/div[2]/h2} - {xpath://*[@id="container-body"]/div[2]/div[2]/h4/span[1]/text()} | NASA Astrobiology Institute',
    '{xpath://*[@id="container-body"]/div[2]/div[2]/h3/text()} - Annual Report | NASA Astrobiology Institute': 'xpath://*[@id="container-body"]/div[2]/div[2]/h3/text() - Annual Report | NASA Astrobiology Institute',
    '{xpath://*[@id="container-body"]/div[2]/div[2]/ol/li/h3} - Article | NASA Astrobiology Institute': 'xpath://*[@id="container-body"]/div[2]/div[2]/ol/li/h3 - Article | NASA Astrobiology Institute',
    "All Things Electric and Magnetic - {xpath:/html/body/div[1]/center[1]/table/tbody/tr/td[2]/font/center/h1/i}": "All Things Electric and Magnetic - xpath:/html/body/div[1]/center[1]/table/tbody/tr/td[2]/font/center/h1/i",
    'Tutorial - {xpath://*[@id="Analyzing-interstellar-reddening-and-calculating-synthetic-photometry"]}': 'Tutorial - xpath://*[@id="Analyzing-interstellar-reddening-and-calculating-synthetic-photometry"]',
    'Health & Air Quality - {xpath://*[@id="block-views-block-hero-block-7"]/div/div/div[2]/div/div/div[2]/div/p}': 'Health & Air Quality - xpath://*[@id="block-views-block-hero-block-7"]/div/div/div[2]/div/div/div[2]/div/p',
    'News - {xpath://*[@id="left-column"]/h2} - {xpath://*[@id="left-column"]/p[1]}': 'News - xpath://*[@id="left-column"]/h2} - xpath://*[@id="left-column"]/p[1]',
    'JWST {xpath://*[@id="stsci-content"]/div/div/h2} - {title}': 'JWST xpath://*[@id="stsci-content"]/div/div/h2 - {title}',
    '{xpath://*[@id="container-body"]/div[2]/div[2]/ol/li/h2} | NASA Astrobiology Institute': 'xpath://*[@id="container-body"]/div[2]/div[2]/ol/li/h2 | NASA Astrobiology Institute',
    'Directory - {xpath://*[@id="container-body"]/div[2]/div[2]/div[1]/h2/text()} | NASA Astrobiology Institute': 'Directory - xpath://*[@id="container-body"]/div[2]/div[2]/div[1]/h2/text() | NASA Astrobiology Institute',
    'Conference and School Funding - {xpath://*[@id="container-body"]/div[2]/div[2]/ol/li/h3/text()} | NASA Astrobiology Institute': 'Conference and School Funding - xpath://*[@id="container-body"]/div[2]/div[2]/ol/li/h3/text() | NASA Astrobiology Institute',
    'Seminars - {xpath://*[@id="container-body"]/div[2]/div[2]/div/h2} | NASA Astrobiology Institute': 'Seminars - xpath://*[@id="container-body"]/div[2]/div[2]/div/h2 | NASA Astrobiology Institute',
    'Team Members - {xpath://*[@id="container-body"]/div[2]/div[2]/div[1]/h2/text()} | NASA Astrobiology Institute': 'Team Members - xpath://*[@id="container-body"]/div[2]/div[2]/div[1]/h2/text() | NASA Astrobiology Institute',
    'Teams - {xpath://*[@id="container-body"]/div[2]/div[2]/div[1]/h2/text()} | NASA Astrobiology Institute': 'Teams - xpath://*[@id="container-body"]/div[2]/div[2]/div[1]/h2/text() | NASA Astrobiology Institute',
    '{xpath://*[@id="page"]/section[3]/div/article/header/h2}': 'xpath://*[@id="page"]/section[3]/div/article/header/h2',
    '{xpath://*[@id="page"]/section[1]/div/header/h2}': 'xpath://*[@id="page"]/section[1]/div/header/h2',
    '{xpath://*[@id="page"]/section[1]/div/header/h2} - News by Column': 'xpath://*[@id="page"]/section[1]/div/header/h2 - News by Column',
}
