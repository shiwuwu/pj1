Feature: 手势与滑动操作
    验证列表滑动、滑动手势和 Toast 消息

    Background:
        Given @device_ready
        And @app_installed("com.example.app")

    Scenario: 列表上下滑动
        When @launch_app("com.example.app")
        And @wait_id("content_list")
        Then @swipe_up("content_list")
        And @swipe_down("content_list")

    Scenario: Toast 消息验证
        When @launch_app("com.example.app")
        And @wait_id("submit_button")
        And @click_id("submit_button")
        Then @toast_contains("操作成功")

    Scenario: 双击放大内容
        When @launch_app("com.example.app")
        And @wait_id("content_area")
        Then @double_tap("content_area")
        And @screenshot("after_double_tap")
