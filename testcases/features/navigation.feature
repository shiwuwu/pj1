Feature: 页面导航与跳转
    验证 Tab 切换、页面跳转和返回操作

    Background:
        Given @device_ready
        And @app_installed("com.example.app")

    Scenario: Tab 切换后页面内容正确
        When @launch_app("com.example.app")
        And @wait_text("首页")
        And @click_text("推荐")
        Then @verify_text("推荐详情")
        And @verify_page_contains("detail_content")

    Scenario: 返回按钮回到上一页
        When @launch_app("com.example.app")
        And @wait_text("首页")
        And @click_text("设置")
        And @verify_text("设置页面")
        Then @go_back
        And @verify_text("首页")

    Scenario: 多次跳转后连续返回
        When @launch_app("com.example.app")
        And @wait_text("首页")
        And @click_text("我的")
        And @click_text("设置")
        And @verify_text("设置页面")
        Then @go_back
        And @go_back
        And @verify_text("首页")
