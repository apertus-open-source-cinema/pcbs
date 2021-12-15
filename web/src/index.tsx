import ReactDOM from "react-dom";
import { FullList, SingleBoard, SpecificSingleBoard } from "./App";
import { HashRouter, Routes, Route } from "react-router-dom";

const app = document.getElementById("app");
ReactDOM.render(
    <HashRouter>
        <Routes>
            <Route index element={<FullList />} />
            <Route path="boards/:board" element={<SingleBoard />} />
            <Route path="boards/:board/:version/:variant/:assemblyVariant" element={<SpecificSingleBoard />} />
        </Routes>
    </HashRouter>,
    app
);
