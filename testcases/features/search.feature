Feature: 搜索功能
    验证关键字搜索、搜索结果展示

    Background:
        Given @device_ready
        And @app_installed("com.example.app")

    Scenario: 输入关键字搜索
        When @launch_app("com.example.app")
        And @wait_id("search_icon")
        And @click_id("search_icon")
        And @type_into("search_input", "HarmonyOS")
        And @press_enter
        Then @search_not_empty
        And @screenshot("search_result")

    Scenario: 清空搜索历史
        When @launch_app("com.example.app")
        And @wait_id("search_icon")
        And @click_id("search_icon")
        And @click_id("clear_history")
        Then @verify_text("暂无搜索历史")
