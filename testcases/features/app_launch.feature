Feature: 应用启动与首页验证
    验证应用冷启动、热启动及首页关键元素存在性

    Background:
        Given @device_ready
        And @app_installed("com.example.app")

    Scenario: 应用冷启动并验证首页元素
        When @launch_app("com.example.app")
        Then @app_launched
        And @verify_text("首页")
        And @verify_id("main_tab_bar")
        And @screenshot("homepage")

    Scenario: 应用从后台恢复
        When @launch_app("com.example.app")
        And @go_home
        And @relaunch_app("com.example.app")
        Then @app_launched
        And @verify_text("首页")
