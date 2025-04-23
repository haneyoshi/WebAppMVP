import ListGroup from "./components/ListGroup";
function App(){
  const items = ["New York", "San Francisco", "Tokyo", "London", "Paris"];
  const handleSelectItem = (item: string) =>{
    console.log(item);
  }
  return <div><ListGroup items={items} heading="Cities" onSelectItem={handleSelectItem}></ListGroup></div>
  //<div><Message /></div>
}

export default App;