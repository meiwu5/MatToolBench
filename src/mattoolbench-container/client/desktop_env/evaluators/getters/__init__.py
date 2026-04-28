from .chrome import (
    get_default_search_engine,
    get_cookie_data,
    get_bookmarks,
    get_open_tabs_info,
    get_pdf_from_url,
    get_shortcuts_on_desktop,
    get_history,
    get_page_info,
    get_enabled_experiments,
    get_chrome_language,
    get_chrome_font_size,
    get_profile_name,
    get_number_of_search_results,
    get_googledrive_file,
    get_active_tab_info,
    get_enable_do_not_track,
    get_enable_enhanced_safety_browsing,
    get_new_startup_page,
    get_find_unpacked_extension_path,
    get_data_delete_automacally,
    get_active_tab_html_parse,
    get_active_tab_url_parse,
    get_gotoRecreationPage_and_get_html_content,
    get_url_dashPart,
    get_active_url_from_accessTree,
    get_find_installed_extension_name,
    get_info_from_website
)
from .file import get_cloud_file, get_vm_file, get_cache_file, get_content_from_vm_file, get_vm_file_exists_in_vm_folder
from .fileexplorer import (
    get_vm_folder_exists_in_documents, 
    get_vm_file_exists_in_desktop,
    get_are_files_sorted_by_modified_time,
    get_is_details_view,
    get_all_png_file_names,
    get_zipped_folder_in_desktop,
    get_is_all_docx_in_archive,
    get_is_file_hidden,
    get_vm_active_window_title,
    get_is_directory_read_only_for_user,
    get_are_all_images_tagged,
    get_is_file_desktop,
    get_vm_library_folders,
    get_is_files_moved_downloads,
    get_is_file_saved_desktop
)
from .general import get_vm_command_line, get_vm_terminal_output, get_vm_command_error
from .gimp import get_gimp_config_file
from .impress import get_audio_in_slide, get_background_image_in_slide
from .info import get_vm_screen_size, get_vm_window_size, get_vm_wallpaper, get_list_directory
from .misc import get_rule, get_accessibility_tree, get_rule_relativeTime, get_time_diff_range
from .replay import get_replay
from .vlc import get_vlc_playing_info, get_vlc_config, get_default_video_player
from .vscode import get_vscode_config
from .calc import get_conference_city_in_order
from .microsoftpaint import (
    get_is_red_circle_present_on_canvas,
    get_image_dimension_matches_input
)
from .windows_clock import get_check_if_timer_started, get_check_if_world_clock_exists
from .edge import get_profile_name_from_edge, get_favorites, get_cookie_data_for_edge, get_history_for_edge, get_enable_do_not_track_from_edge, get_enable_enhanced_safety_browsing_from_edge, get_data_delete_automacally_from_edge, get_edge_font_size, get_default_search_engine_from_edge, get_url_shortcuts_on_desktop
from .settings import (
    get_night_light_state,
    get_default_browser,
    get_storage_sense_run_frequency,
    get_active_hours_of_user_to_not_interrupt_for_windows_updates,
    get_system_timezone,
    get_desktop_background,
    get_system_notifications
)
from .msedge import (
    get_edge_home_page,
    get_validate_pwa_installed,
    get_edge_default_download_folder
)
from .origin import (
    get_validate_image_with_model,
    get_validate_file_with_model,
    get_file_contains,
    get_file_exists,
    get_file_exists_nonempty,
    get_origin_aesthetic_score,
)

from .jade import (
    get_check_file_opened_jade,
    get_check_peak_finding,
    get_check_peak_add_two,
    get_check_background_removal,
    get_check_smoothing,
    get_check_smoothing_and_background,
    get_check_axis_switch,
    get_check_axes_menu,
    get_check_wpf_refinement,
    get_check_refinement_result,
    get_check_dialog_title_jade,
    get_check_search_match_elements
)
from .avantage import (
    get_check_multiple_files_imported,
    get_check_image_zoom,
    get_check_stacked_graph,
    get_check_duplicate_files_imported,
    get_check_background_added_successfully,
    get_check_dialog_parameter,
    get_check_dialog_exists,
    get_check_grid_layout,
    get_check_energy_axis_reversed,
    get_check_file_duplicated
)

from .dm import (
    get_check_file_import,
    get_check_ocr_text,
    get_check_drawing_tool,
    get_check_text_color,
    get_check_border_color,
    get_check_checkbox_selected,
    get_check_dialog_opened_dm,
    get_check_data_bar_by_text,
    get_check_roi_copy_and_enlarge,
    get_check_filled_box_with_corners,
    get_check_text_count_in_dialog,
)

from .vesta import (
    get_check_file_opened_vesta,
    get_check_standard_orientation,
    get_check_rotation_90_up,
    get_check_translation,
    get_check_style_change,
    get_check_atom_info_dialog,
    get_check_atom_deletion,
    get_check_bond_display,
    get_check_zoom,
    get_check_axes_toggle,
    get_check_dialog_opened_vesta,
    get_check_polyhedral_style,
    get_check_orientation_vector,
    get_check_lattice_plane,
    get_check_multiple_lattice_planes,
    get_check_boundary_settings,
    get_check_bonds_cleared,
    get_check_atom_coordinates_in_edit_data,
    get_check_properties_field
)

from .ms import (
    get_check_file_in_title,
    get_check_dialog_title_ms,
    get_check_text_keyword,
    get_check_field_value,
    get_check_visual_similarity,
    get_check_multiple_fields,
)