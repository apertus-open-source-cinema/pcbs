import preview_top from "../../boards/*_top-preview.webp";
import preview_bottom from "../../boards/*_bottom-preview.webp";

import full_top from "../../boards/*_top.webp";
import full_bottom from "../../boards/*_bottom.webp";
import licenses from "../../LICENSES/*.txt";
import brds from "../../boards/*.brd";
import schs from "../../boards/*.sch";
import sch_pdfs from "../../boards/*.pdf";
import gerbers from "../../boards/*.zip";
import * as infos from "../../info.json";

function board_infos_to_grouped(infos) {
    let boards = new Map();

    for (const board of infos) {
        let {name, version, tag} = board;
        if (tag === null) {
            tag = "default";
        }

        if (!boards.has(name)) {
            boards.set(name, new Map());
        }
        const versions = boards.get(name);
        if (!versions.has(version)) {
            versions.set(version, new Map())
        }
        versions.get(version).set(tag, board);
    }

    return boards;
}


export const boards = board_infos_to_grouped(infos);

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
