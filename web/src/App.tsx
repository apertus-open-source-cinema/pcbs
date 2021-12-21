{/*
SPDX-FileCopyrightText: © 2021 Robin Ole Heinemann <robin.ole.heinemann@gmail.com>

SPDX-License-Identifier: AGPL-3.0-only
*/}

import {boards, board_data, licenses, schs, brds, sch_pdfs, gerbers} from "./data.ts";

import {
    Link,
    Button,
    Card,
    CardContent,
    Grid,
    Typography,
    FormControl,
    Select,
    MenuItem,
    Box
} from "@mui/material";

import {useState} from "react";
import {useParams, Link as RouterLink} from "react-router-dom";

function CopyInfo(props) {
    const info = props.info;
    return <>
        {info["copyright"].map((copy, i) => <Typography key={i}>Copyright: {copy}</Typography>)}
        <Typography>License: <License license={info["license"]}/></Typography>
    </>
}

function License(props) {
    const spdx_id = props.license;
    return <Link href={licenses[spdx_id]}>{spdx_id}</Link>
}

function select_parameters(info, version: String | null, tag: String | null, variant: String | null) {
    if (version === null) {
        version = sorted_choices(info.keys())[0];
    }
    const tags = info.get(version);
    if (tag === null) {
        tag = tags.keys().next().value;
    }
    const variants = tags.get(tag)["variants"];
    if (variant === null) {
        if (Array.from(variants.values()).includes("Beta")) {
            variant = "Beta";
        } else {
            variant = sorted_choices(variants.values())[0];
        }
    }
    return [version, tag, variant] ;
}

function Board(props) {
    const name = props.name;
    const board = props.board;
    const [[version, tag, variant], setSelected] = useState(select_parameters(board, null, null, null));
    const selected = board.get(version).get(tag);
    const base = selected["base"];

    return <Grid item>
        <Card>
            <CardContent>
                <Link color="inherit" underline="hover" to={`/boards/${name}`} component={RouterLink}>
                    <Typography variant='h4'>{name}</Typography>
                </Link>
                <Grid container>
                    <Grid item xs={4}>
                        <Grid container direction="column" spacing={2}>
                            <Grid item>
                                <Typography variant='h6'>Schematic:</Typography>
                                <CopyInfo info={selected["sch"]}/>
                                <Grid container spacing={2}>
                                    <Grid item><Button variant="contained"
                                                       download={`${base}.sch`}
                                                       href={schs[base]}>.sch</Button></Grid>
                                    <Grid item><Button variant="contained"
                                                       download={`${base}-${variant}.pdf`}
                                                       href={sch_pdfs[`${base}-${variant}`]}>.pdf</Button></Grid>
                                </Grid>
                            </Grid>
                            <Grid item>
                                <Typography variant='h6'>Board:</Typography>
                                <CopyInfo info={selected["brd"]}/>
                                <Grid container spacing={2}>
                                    <Grid item><Button variant="contained" download={`${base}-${variant}.brd`} href={brds[`${base}-${variant}`]}>.brd</Button></Grid>
                                    <Grid item><Button variant="contained" download={`${base}-${variant}.zip`} href={gerbers[`${base}-${variant}`]}>Gerbers</Button></Grid>
                                </Grid>
                            </Grid>
                        </Grid>
                    </Grid>
                    <Grid item xs={7}>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', width: 1100 }}>
                            <a href={board_data[`${base}-${variant}`]["full"]["top"]}>
                                <img src={board_data[`${base}-${variant}`]["preview"]["top"]} loading="lazy" />
                            </a>
                            <a href={board_data[`${base}-${variant}`]["full"]["bottom"]}>
                                <img src={board_data[`${base}-${variant}`]["preview"]["bottom"]} loading="lazy" />
                            </a>
                        </Box>
                    </Grid>
                    <Grid item xs={1}>
                        <Grid container direction="column" spacing={2}>
                            <MaybeChooser
                                name={"Version:"}
                                value={version}
                                choices={board.keys()}
                                onChange={(new_version) => setSelected(select_parameters(board, new_version, null, null))}
                            />
                            <MaybeChooser
                                name={"Variant:"}
                                value={tag}
                                choices={board.get(version).keys()}
                                onChange={(new_tag) => setSelected(select_parameters(board, version, new_tag, null))}
                            />
                            <MaybeChooser
                                name={"Assembly Variant:"}
                                value={variant}
                                choices={board.get(version).get(tag)["variants"].values()}
                                onChange={(new_variant) => setSelected([version, tag, new_variant])}
                            />
                            <Grid item>
                                <Link to={`/boards/${name}/${version}/${tag}/${variant}`} component={RouterLink}>
                                    Direct link
                                </Link>
                            </Grid>
                        </Grid>
                    </Grid>
                </Grid>
            </CardContent>
        </Card>
    </Grid>;
}

export function FullList(props) {
    const bs = props.boards ?? boards;
    return <Grid container alignItems="center" justifyContent="center">
        <Grid item container direction="column" alignItems="stretch" spacing={1} justifyContent="center" sx={{ width: 1800 }}>
            {Array.from(bs.entries(), ([name, versions]) => <Board key={name} name={name} board={versions}/>)}
        </Grid>
    </Grid>
}

export function SingleBoard() {
    const { board } = useParams();
    const fakeBoards = new Map();
    fakeBoards.set(board, boards.get(board));
    return <FullList boards={fakeBoards} />
}

export function SpecificSingleBoard() {
    const { board, variant, version, assemblyVariant } = useParams();
    const fakeBoards = new Map();
    fakeBoards.set(board, new Map());
    const versions = fakeBoards.get(board);
    versions.set(version, new Map());
    const copiedBoard = Object.assign({}, boards.get(board).get(version).get(variant));
    copiedBoard["variants"] = [assemblyVariant];
    versions.get(version).set(variant, copiedBoard);

    return <FullList boards={fakeBoards} />
}

function sorted_choices(c) {
    const choices = Array.from(c);
    const collator = new Intl.Collator(undefined, {numeric: true, sensitivity: 'base'});
    choices.sort(collator.compare);
    return choices.reverse();
}

function MaybeChooser(props) {
    const choices = sorted_choices(props.choices);
    let value = <></>
    if (choices.length > 1) {
        return <Grid item><FormControl>
            <Typography>{props.name}</Typography>
            <Select value={props.value} onChange={(event) => props.onChange(event.target.value)}>
                {choices.map((choice) => <MenuItem key={choice} value={choice}>{choice}</MenuItem>)}
            </Select>
        </FormControl></Grid>;
    } else {
        if (choices[0] != "default" && choices[0] !== null) {
            value = <Grid item>
                <Typography>{props.name}</Typography>
                <Typography>{choices[0]}</Typography>
            </Grid>;
        }
    }
    return value;
}
