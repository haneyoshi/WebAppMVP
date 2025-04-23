//import { Fragment } from "react";
import { useState } from "react";
interface ListGroupProps {
    items: string[];
    heading: string;
    onSelectItem:(item: string) => void;
}

function ListGroup({items, heading, onSelectItem}: ListGroupProps) {
    
    const checkEmpty = () => {
        items.length == 0 && <p>no items found</p>;
        //In JavaScript "&&" works as:
        // true && "when first statement is true"=> when first statement is true
        // false && "never print, since first statement is false => false (does nothing)
    };
    const [selectedIndex, setSelectedIndex] = useState(-1);
    
    
    return (
        <>
      <h1>{heading}</h1>
      {checkEmpty()}
      {/* if empty, inform "message"*/}
      {/* if false (not empty), does nothing, continue */}
      <ul className="List-Group">
        {/* in the middle of mark-up section, only elements are allowed, therefore "{}" is needed to treat functions as elements */}
        {/* JSX does not have for loop */}
        {items.map((item, index) => (
          <li
            className={selectedIndex === index ? 'list-group-item active':'list-group-item'}
//             className="list-group-item"
// style={{ backgroundColor: selectedIndex === index ? 'lightblue' : '' }}

            key={item}
            onClick={() => {setSelectedIndex(index);onSelectItem(item);}}
          >
            {item}
          </li>
        ))}
      </ul>
    </>
  );
}

export default ListGroup;
