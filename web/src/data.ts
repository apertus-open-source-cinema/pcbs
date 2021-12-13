import preview_top from "../../boards/*_top-preview.png";
import preview_bottom from "../../boards/*_bottom-preview.png";

import full_top from "../../boards/*_top.png";
import full_bottom from "../../boards/*_bottom.png";
import licenses from "../../LICENSES/*.txt";
import brds from "../../boards/*.brd";
import schs from "../../boards/*.sch";
import sch_pdfs from "../../boards/*.pdf";
import gerbers from "../../boards/*.zip";

export { licenses, brds, schs, sch_pdfs, gerbers };
export const board_data = Object.keys(preview_top).reduce((obj, name) => {
    obj[name] = {
        "preview": {
            "top": preview_top[name],
            "bottom": preview_bottom[name],
        },
        "full": {
            "top": full_top[name],
            "bottom": full_bottom[name],
        },
    };
    return obj;
}, {})
