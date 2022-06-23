# Changelog

All notable changes to this project will be documented in this file.

## [0.9.0a1.dev11] - 2022-06-23

<details>

### 7c277c3

- refactor!: use httpx in qqqr
- refactor!: new qqqr structure

### 6a70077

- refactor: move aioqzone login event to qqqr

### b91a2a8

- test: update tests
- feat(api)!: MixedLoginman is not subclass of UpLoginman and QrLoginman
- proj: remove aiohttp from project
- feat(api): capture video field in msgdetails
- feat(api): add from_floatview for VideoInfo

### 766b9ac

- feat: remove setting UA support
- fix: ImportError of multidict
- feat: handle GeneratorExit

### 5638ae4

- refactor!: feeds3_html_more returns FeedMoreResp object instead of tuple
- refactor: remove request method in LoginBase
- perf: add slots for dataclass types on py310 and above
- style: remove type ignore anno. in DummyQapi
- test: update to use ClientAdapter

### 5cff8d9

- refactor: mv js files into archive
- feat!: add TcaptchaSession in captcha

### 5cd3baa

- fix: `AsyncClient` was not imported
- ci: rollback test.yml

### 605729c

- ci: fix ci file syntax error

### 37e5986

- test: fix connect pool not cleared when client exit
- fix: response not closed in `__aexit__`

### 9397ee8

- proj: add changelog generator config
- ci: use generated changelog as pr body
- security: update numpy 1.21.x

### 923de6b


- ci: add job trigger flag

### ab53ee3

- ci: fix wrong pr body

### 20ac0c2

- fix!: new captcha protocol




</details>
